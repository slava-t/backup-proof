from datetime import datetime, timezone
import os
from pathlib import Path
from shutil import move
import shutil
import subprocess
import sys
import time
import traceback

from backup_confirm.logger import get_logger
from backup_confirm.notification import notify_report, notify
from backup_confirm.config import get_config, reset_config
from backup_confirm.paths import (
  ENC_PROCESS_DIR,
  VERIFIED_DIR,
  FAILED_DIR,
  ZPOOL_STATUS_PATH
)

from backup_confirm.report import (
  create_process_report,
  add_complete_step,
  create_zpool_status_failures_report
)
from backup_confirm.utils import (
  is_fid,
  parse_process_name,
  parse_zpool_status,
  read_from_yaml_file,
  write_to_yaml_file
)
#TODO for testing
SCAN_AND_COMPLETE_INTERVAL = 120 #2 minutes
#SCAN_AND_COMPLETE_INTERVAL = 1 #2 minutes

DONE_PREFIX = 'done-'
MAX_PROCESS_AGE = 24 * 3600 #24 hours

ZPOOL_CHECK_INTERVAL = 3600 #1 hour
MAX_ZPOOL_STATUS_AGE = 3600 * 4 #4 hours
MOUNT_DETECTION_INTERVAL = 3600 #1 hour

DISK_USAGES_CHECK_INTERVAL = 3600 #1 hour

KEEP_VERIFIED = 2 #30
KEEP_FAILED = 2 #10

DEFAULT_MAX_DISK_USAGE_RATE = 0.75

logger = get_logger('complete')

def get_env_dir(base_dir, process_descriptor):
  env_dir = os.path.join(
    base_dir,
    process_descriptor['prod'],
    process_descriptor['env']
  )
  os.makedirs(env_dir, mode=0o600, exist_ok=True)
  return env_dir

def move_process(process_descriptor, mark_as_done, reason = None):
  try:
    process_name = process_descriptor['orig']
    logger.info('Moving process \'{}\': mark_as_done={}, reason={}'.format(
      process_name,
      mark_as_done,
      reason
    ))
    process_dir = os.path.join(ENC_PROCESS_DIR, process_name)
    if mark_as_done:
      done_path = os.path.join(
        ENC_PROCESS_DIR,
        '{}{}'.format(DONE_PREFIX, process_name)
      )
      Path(done_path).touch()
    target_dir = FAILED_DIR if reason else VERIFIED_DIR
    target_env_dir = get_env_dir(target_dir, process_descriptor)
    target_process_dir = os.path.join(target_env_dir, process_descriptor['fid'])
    logger.info('Moving directory \'{}\' to \'{}\''.format(
      process_dir,
      target_process_dir
    ))
    move(process_dir, target_process_dir)
    status = {
      'status': 'failed' if reason else 'success'
    }
    if reason:
      logger.info('Failed completting reason \'{}\''.format(reason))
      status['reason'] = reason
    logger.info('Status for \'{}\': {}'.format(process_name, status))
    write_to_yaml_file(status, os.path.join(target_process_dir, 'status.yaml'))
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Processing error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))
  return False

def docker_compose_down(process_dir):
  try:
    logger.info('Shutting down process \'{}\''.format(process_dir))
    result = subprocess.run(
      [
        '/usr/local/bin/docker-compose',
        'down'
      ],
      cwd=process_dir
    )
    logger.info('Docker-compose return code: {}'.format(result.returncode))
    return result.returncode == 0
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Shutting process \'{}\' down failed: {}'.format(
      process_dir,
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
  return False

def prune_env_dir(target_dir, keep):
  try:
    sorted_dirnames = sorted(os.listdir(target_dir), reverse=True)
    fids = [x for x in sorted_dirnames if is_fid(x)]
    to_delete = fids[keep:]
    for fid in to_delete:
      shutil.rmtree(os.path.join(target_dir, fid))
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in check_and_complete function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
  return False

def shutdown_process(report_data, process_descriptor):
  process_dir = os.path.join(ENC_PROCESS_DIR, process_descriptor['orig'])
  result = docker_compose_down(process_dir)
  add_complete_step(
    report_data,
    'shutdown_process',
    'Shutdown process docker container(s)',
    result
  )

def prune_failed_dirs(report_data, process_descriptor):
  env_dir = get_env_dir(FAILED_DIR, process_descriptor)
  result = prune_env_dir(env_dir, KEEP_FAILED)
  add_complete_step(
    report_data,
    'prune_failed_dirs',
    'Prune failed process directories',
    result
  )

def prune_verified_dirs(report_data, process_descriptor):
  env_dir = get_env_dir(VERIFIED_DIR, process_descriptor)
  result = prune_env_dir(env_dir, KEEP_VERIFIED)
  add_complete_step(
    report_data,
    'prune_verified_dirs',
    'Prune verified process directories',
    result
  )

def move_process_to_history(report_data, process_descriptor):
    process_name = process_descriptor['orig']
    logger.info('Moving process \'{}\' to history'.format(process_name))
    status = report_data.get('valid_data', False)
    move_result = False
    if status:
      move_result = move_process(process_descriptor, True)
    else:
      move_result = move_process(
        process_descriptor,
        True,
        reason = 'Failed data validation'
      )
    add_complete_step(
      report_data,
      'move_process',
      'Move processed data to history',
      move_result
    )

def check_and_complete(process_descriptor):
  report_data = {}
  try:
    process_name = process_descriptor['orig']
    process_path = os.path.join(ENC_PROCESS_DIR, process_name)
    status = read_from_yaml_file(os.path.join(process_path, 'status.yaml'))
    if status['status'] != 'end':
      return
    logger.info('Completing starts for \'{}\''.format(process_path))
    report_data = create_process_report(process_descriptor)
    logger.info('Invoking shutdown_process for \'{}\''.format(process_name))
    shutdown_process(report_data, process_descriptor)
    logger.info('Invoking move_process_to_history for \'{}\''.format(
      process_name
    ))
    move_process_to_history(report_data, process_descriptor)
    logger.info('Invoking prune_verified_dirs for \'{}\''.format(process_name))
    prune_verified_dirs(report_data, process_descriptor)
    logger.info('Invoking prune_failed_dirs for \'{}\''.format(process_name))
    prune_failed_dirs(report_data, process_descriptor)
    logger.info('Invoking notify for \'{}\''.format(process_name))
    notify_report(report_data)
    logger.info('Completion finished for \'{}\''.format(process_name))
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in check_and_complete function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))

def prune_done_markers(names, process_descriptor):
  try:
    now = datetime.now(timezone.utc)
    for name in names:
      parsed = parse_process_name(name)
      if (
        parsed and
        parsed['prod'] == process_descriptor['prod'] and
        parsed['env' ] == process_descriptor['env'] and
        (now - parsed['time']).total_seconds() > MAX_PROCESS_AGE
      ):
        marker_name = '{}{}'.format(DONE_PREFIX, name)
        marker_path = os.path.join(ENC_PROCESS_DIR, marker_name)
        os.remove(marker_path)
  except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      logger.error('Error in prune_done_markers function: {}'.format(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
      ))

def scan_and_complete():
  try:
    reset_config()
    now = datetime.now(timezone.utc)
    all_process_names = os.listdir(ENC_PROCESS_DIR)
    done = set([
      x[len(DONE_PREFIX):] for x in all_process_names if x.startswith(DONE_PREFIX)
    ])
    process_names = [x for x in all_process_names if x not in done]
    for process_name in process_names:
      process_descriptor = parse_process_name(process_name)
      if process_descriptor is None:
        continue
      process_age = (now - process_descriptor['time']).total_seconds()
      if process_age > MAX_PROCESS_AGE:
        move_process(process_name, False, reason = 'Timed out')
        continue
      check_and_complete(process_descriptor)
      prune_done_markers(list(done), process_descriptor)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in scan_and_complete function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))

  

def check_zpool_status():
  config = get_config() or {}
  handle = config.get('zpool_status_handle')
  failure_data = {
    'success': False,
    'title': 'Backup zpool status failure(\'{}\')'.format(handle)
  }
  try:
    now = datetime.now(timezone.utc).timestamp()
    expected_count = config.get('zpool_expected_online_count')
    if expected_count is not None and handle is not None:
      if not os.path.isfile(ZPOOL_STATUS_PATH):
        failure_data['text'] = 'Could not find \'{}\' file'.format(
          ZPOOL_STATUS_PATH
        )
      elif now - os.path.getmtime(ZPOOL_STATUS_PATH) > MAX_ZPOOL_STATUS_AGE:
        failure_data['text'] = 'File \'{}\' is too old'.format(
          ZPOOL_STATUS_PATH
        );
      else:
        zpool_status = parse_zpool_status(ZPOOL_STATUS_PATH)
        if zpool_status is None:
          raise Exception('Could not get zpool status from \'{}\''.format(
            ZPOOL_STATUS_PATH
          ))
        failure_data['text'] = create_zpool_status_failures_report(zpool_status)
    if failure_data.get('text') is None:
      logger.info('Sending success zpool status notification for \'{}\''.format(
        handle
      ))
      return notify(
        handle,
        {
          'success': True,
        }
      )
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in check_zpool_status function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
    failure_data['text'] = 'An error occurred while checking the status'
  logger.info('Sending failure zpool status notification for \'{}\''.format(
    handle
  ))
  notify(handle, failure_data)

def check_disk_usages():
  config = get_config() or {}
  handle = config.get('disk_usages_handle')
  disk_usages = config.get('disk_usages') or []
  failure_data = {
    'success': False,
    'title': 'Disk usage status failure(\'{}\')'.format(handle)
  }
  try:
    lines = []
    for disk_usage in disk_usages:
      path = disk_usage.get('path')
      if path is None:
        logger.info('No path provided for a disk usage config')
        lines.append('  Missing \'path\' config entry')
      else:
        max_rate = disk_usage.get('max_rate')
        if max_rate is None:
          max_rate = DEFAULT_MAX_DISK_USAGE_RATE
        _, u, f = shutil.disk_usage(path)
        rate = round(u / (u + f), 2)
        if rate > max_rate:
          lines.append('  Usage rate for \'{}\' is {}  which exceeds {}'.format(
            path,
            rate,
            max_rate
          ))
    if len(lines) > 0:
      failure_data['text'] = (
        'The following disk usage failures occurred:\n{}'
      ).format('\n'.join(lines))
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in check_disk_usages function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
    failure_data['text'] = 'An error occurred while checking disk usages'
  logger.info('Sending disk usages failure notification for \'{}\''.format(
    handle
  ))
  notify(handle, failure_data)

def check_mount_status():
  config = get_config() or {}
  paths = config.get('mount_status_paths') or []
  handle = config.get('mount_status_handle')
  failure_data = {
    'success': False,
    'title': 'Backup mounts status failure(\'{}\')'.format(handle),
  }
  try:
    if len(paths) < 1:
      failure_data['text'] = (
        'No mount check paths has been detected in the configuration'
      )
    else:
      lines = []
      for mount_check_path in paths:
        if not os.path.exists(mount_check_path):
          lines.append('   {}'.format(mount_check_path))
      if len(lines) > 0:
        failure_data['text'] = 'The following paths do not exist:\n{}'.format(
          '\n'.join(lines)
        )

    if failure_data.get('text') is None:
      logger.info('Sending success enc mount notification for \'{}\''.format(
        handle
      ))
      return notify(
        handle,
        {
          'success': True,
        }
      )
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in check_mount_status function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
    failure_data['text'] = 'An error occurred while checking the status'

  logger.info('Sending failure enc mount notification for \'{}\''.format(
    handle
  ))
  notify(handle, failure_data)

def main():
  logger.info('Start completting service')
  count = 1
  while True:
    try:
      if count % SCAN_AND_COMPLETE_INTERVAL == 0:
        scan_and_complete()
      if count % ZPOOL_CHECK_INTERVAL == 0:
        check_zpool_status()
      if count % MOUNT_DETECTION_INTERVAL == 0:
        check_mount_status()
      if count % DISK_USAGES_CHECK_INTERVAL == 0:
        check_disk_usages()
      count += 1
      if count == 10**9:
        count = 1
      time.sleep(1)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      logger.error('Error in complete main function: {}'.format(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
      ))

