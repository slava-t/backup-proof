import os
import secrets
import subprocess
import traceback
import sys
import time

from backup_confirm.confirm_vars import (
  CONFIRM_ENVIRONMENT_VAR, CONFIRM_PROCESS_PATH_VAR,
  CONFIRM_PROD_ENV_ID_VAR,
  CONFIRM_PRODUCT_VAR,
  CONFIRM_REPO_NAME_VAR,
  CONFIRM_TIMESTAMP_ID_VAR,
  CONFIRM_FID_VAR,
  CONFIRM_PROCESS_LOG_VAR,
  CONFIRM_PROCESS_PATH, CONFIRM_ZONE_VAR
)

from backup_confirm.command_runner import run_command
from backup_confirm.context import get_process_context
from backup_confirm.logger import get_logger
from backup_confirm.paths import (
  ENC_PROCESS_DIR
)

from backup_confirm.step import (
  get_step_context,
  get_next_step,
  create_star_step,
  save_step_status
)
from backup_confirm.utils import (
  write_to_yaml_file,
  read_from_yaml_file,
  split_prod_env_id
)
from backup_confirm.vars import BACKUP_PROOF_IMAGE

PROCESS_SCAN_INTERVAL = 1

logger = get_logger('process')

def get_steps_content(confirm_steps_path):
  return {
    'steps': [{
      'name': 'extract_confirm',
      'description': 'Extract \'confirm\' part',
      'command': 'extract_part',
      'params': {
        'part': 'confirm'
      }
    }, {
      'name': 'extract_logs',
      'command': 'extract_part',
      'description': 'Extract \'logs\' part',
      'params': {
        'part': 'logs'
      }
    }, {
      'name': 'verify_sha1sum_confirm',
      'description': 'Verify sha1sum for \'confirm\' part',
      'command': 'verify_sha1sum',
      'params': {
        'part': 'confirm'
      },
      'dependencies': ['extract_confirm']
    }, {
      'name': 'verify_sha1sum_logs',
      'description': 'Verify sha1sum for \'logs\' part',
      'command': 'verify_sha1sum',
      'params': {
        'part': 'logs'
      },
      'dependencies': ['extract_logs']
    }, {
      'name': 'create_confirm_steps_yaml',
      'description': 'Create yaml file for confirmation steps from confirm/spec.yaml',
      'command': 'create_confirm_steps_yaml',
      'dependencies': ['verify_sha1sum_confirm', 'verify_sha1sum_logs']
    }, {
      'name': 'create_confirm_steps',
      'description': 'Create confirmation steps from confirm_steps.yaml',
      'command': '*',
      'params': {
        'path': confirm_steps_path
      },
      'dependencies': ['create_confirm_steps_yaml']
    }, {
      'name': 'check_borg_data',
      'description': 'Run \'borg check\' for borg repo integrity',
      'command': 'check_borg_data',
      'options': [{
        'name': 'check_borg_data',
        'default': True,
        'param': 'enable'
      }]
    }, {
      'name': 'verify_data_status',
      'description': 'Verify data status based on previous steps',
      'command': 'verify_preceeding_steps',
      'params': {
        'status': 'data_status.yaml'
      }
    }, {
      'name': 'publish',
      'description': (
        'Make the parts available for downloading'
      ),
      'command': 'publish',
      'options': [{
        'name': 'publish',
        'default': True,
        'param': 'enable'
      }],
      'dependencies': ['verify_data_status']
    }, {
      'name': 'release',
      'description': (
        'Make the parts available for restoring'
      ),
      'options': [{
        'name': 'release',
        'param': 'enable',
        'default': True
      }],
      'command': 'release',
      'dependencies': ['verify_data_status']
    }, {
      'name': 'mark_verified_in_borg',
      'description': 'Mark the verified parts in borg',
      'command': 'mark_verified_in_borg',
      'dependencies': ['verify_data_status']
    }, {
      'name': 'clean_borg_repo',
      'description': 'Removing old archives from borg repo',
      'command': 'clean_borg_repo'
    }, {
      'name': 'check_borg_repo',
      'description': (
        'Run \'borg check\' for borg repo integrity after repo cleaning'
      ),
      'command': 'check_borg_data',
      'options': [{
        'name': 'check_borg_repo',
        'default': True,
        'param': 'enable'
      }]
    }]
  }

def get_compose_content(vars):
  return {
    'version': '3.5',
    'services': {
      'confirm': {
        'volumes':[
          '/data/confirm:/data/confirm',
          '/data/backup/enc:/backup/enc',
          '/data/backup/var:/backup/var',
          '/data/backup/.config:/backup/.config:ro',

          '/var/run/docker.sock:/var/run/docker.sock',
          '/usr/bin/docker:/usr/bin/docker',
          '/usr/lib/x86_64-linux-gnu/libltdl.so.7:/usr/lib/libltdl.so.7',
        ],
        'image': BACKUP_PROOF_IMAGE,
        'restart': 'unless-stopped',
        'networks': ['borg'],
        'environment': {
          'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'yes',
          CONFIRM_ZONE_VAR: vars['zone'],
          CONFIRM_PROD_ENV_ID_VAR: vars['prod_env_id'],
          CONFIRM_ENVIRONMENT_VAR: vars['environment'],
          CONFIRM_REPO_NAME_VAR: vars['repo_name'],
          CONFIRM_PRODUCT_VAR: vars['product'],
          CONFIRM_PROCESS_PATH_VAR: vars['process_path'],
          CONFIRM_PROCESS_LOG_VAR: os.path.join(
            vars['process_path'],
            'confirm.log'
          ),
          CONFIRM_TIMESTAMP_ID_VAR: vars['id'],
          CONFIRM_FID_VAR: vars['fid']
        },
        'command': '/usr/local/bin/run_confirm_process'
      }
    },
    'networks': {
      'borg': {
        'name': 'borgnet',
        'external': True
      }
    }
  }

def create_process(repo_name, repo, prod_env_id, parts):
  product, environment = split_prod_env_id(prod_env_id)
  confirm_part = parts.get('confirm')
  zone = repo['zone']
  id = confirm_part.get('id')
  fid = confirm_part.get('fid')
  process_id = '{}-{}'.format(prod_env_id, fid)
  process_tmp_id = '{}-{}'.format(process_id, secrets.token_hex(8))
  process_path = os.path.join(ENC_PROCESS_DIR, process_id)
  process_done_path = os.path.join(ENC_PROCESS_DIR, 'done-{}'.format(
    process_id
  ))
  confirm_steps_path = os.path.join(process_path, 'confirm_steps.yaml')
  process_tmp_path = os.path.join(ENC_PROCESS_DIR, process_tmp_id)
  tmp_ctx = get_process_context(process_tmp_path)

  if os.path.isdir(process_path) or os.path.isfile(process_done_path):
    return
  logger.info('Creating process for {} {}'.format(product, environment))
  logger.info('Process path \'{}\''.format(process_path))
  logger.info('Process tmp path \'{}\''.format(process_tmp_path))
  os.mkdir(process_tmp_path, 0o600)
  os.mkdir(tmp_ctx['parts_dir'], 0x600)
  os.mkdir(tmp_ctx['steps_dir'], 0o600)
  write_to_yaml_file({}, tmp_ctx['options'])
  parts_content = {
    'zone': zone,
    'timestamp_id': id,
    'fid': fid,
    'repo': repo_name,
    'product': product,
    'environment': environment,
    'product_env_id': prod_env_id,
    'parts': parts
  }
  write_to_yaml_file(
    parts_content,
    tmp_ctx['parts']
  )

  write_to_yaml_file(
    get_steps_content(confirm_steps_path),
    tmp_ctx['steps']
  )

  write_to_yaml_file(
    {
      'status': 'start'
    },
    tmp_ctx['status']
  )

  write_to_yaml_file(
    get_compose_content({
      'zone': zone,
      'prod_env_id': prod_env_id,
      'environment': environment,
      'repo_name': repo_name,
      'product': product,
      'process_path': process_path,
      'id': id,
      'fid': fid
    }),
    tmp_ctx['docker-compose']
  )
  logger.info('Renaming \'{}\' to \'{}\''.format(
    process_tmp_path,
    process_path
  ))
  os.rename(process_tmp_path, process_path)
  logger.info('running docker compose in \'{}\''.format(process_path));
  subprocess.run(
    [
      '/usr/local/bin/docker-compose',
      'up',
      '-d'
    ],
    cwd=process_path,
    check=True
  )

def create_processes(repo_name, repo, confirm_parts):
  #logger.info('Creating processes: {}'.format(parts))
  for prod_env_id, parts in confirm_parts.items():
    create_process(repo_name, repo, prod_env_id, parts)

def process_step(ctx, stepname):
  ctx = get_step_context(ctx, stepname)
  try:
    status_content = read_from_yaml_file(ctx['step_status'])
    status = status_content.get('status')
    if status in ['run', 'running']:
      return
    if status in {'success', 'failed', 'skipped'}:
      logger.info('Step \'{}\' finished with status \'{}\''.format(
        stepname,
        status.upper()
      ))
      return get_next_step(ctx, stepname)

    if status != 'start':
      raise Exception('Invalid status \'{}\' for step \'{}\''. format(
        stepname,
        status
      ))
    logger.info('*** Processing step \'{}\' ***'.format(stepname))
    save_step_status(ctx, {
      'status': 'run'
    })
    run_command(ctx)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Processing step error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))
    save_step_status(ctx, {
      'status': 'failed'
    })

def start_process(ctx):
  logger.info('Starting process \'{}\''.format(
    ctx['main_dir']
  ))
  step_dirname = create_star_step(ctx, 0, 'star', ctx['steps'])
  status_content = {
    'status': 'step',
    'step': step_dirname
  }
  write_to_yaml_file(status_content, ctx['status'])

def process():
  if not CONFIRM_PROCESS_PATH:
    return
  ctx = get_process_context(CONFIRM_PROCESS_PATH)
  status_content = read_from_yaml_file(ctx['status']) or {}
  status = status_content['status']
  if not status_content['status']:
    raise Exception('No \'status\' in status.yaml')
  if status == 'start':
    start_process(ctx)
    return
  if status == 'end':
    return
  if status != 'step':
    raise Exception('Unexpected status \'{}\''.format(status))
  step = status_content['step']
  result = process_step(ctx, step)
  if result is None:
    return
  if result == 'end':
    status_content = {
      'status': 'end'
    }
    logger.info('Finished all steps')
  else:
    status_content = {
      'status': 'step',
      'step': result
    }
  write_to_yaml_file(status_content, ctx['status'])

def main():
    while True:
      try:
        time.sleep(PROCESS_SCAN_INTERVAL)
        process()
      except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error('Processing error: {}'.format(''.join(
          traceback.format_exception(exc_type, exc_value, exc_traceback)
        )))
