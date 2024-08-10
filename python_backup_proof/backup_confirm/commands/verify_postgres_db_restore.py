import os
import sys
import traceback
import re

from backup_confirm.cluster import (
  create_step_cluster,
  destroy_cluster,
  exec_in_cluster,
  wait_for_success
)

from backup_confirm.logger import get_logger

from backup_confirm.step import (
  get_step_info,
  step_failed,
  step_success,
)

from backup_confirm.utils import is_path_short, is_path_safe

NOTICE_DROP_ROLE_OR_DB_RE = re.compile(
  '^NOTICE:\s+(database|role)\s+.*does not exist, skipping$'
)

ERROR_POSTGRES_USER_EXISTS_RE = re.compile(
  '^ERROR:  role "postgres" already exists$'
)

ERROR_CURRENT_USER_CANNOT_DROP_RE = re.compile(
  '^ERROR:  current user cannot be dropped$'
)

logger = get_logger('verify_postgres_db_restore')

ignore_from_stderr = [
  NOTICE_DROP_ROLE_OR_DB_RE,
  ERROR_CURRENT_USER_CANNOT_DROP_RE,
  ERROR_POSTGRES_USER_EXISTS_RE
]

def log_has_error(log):
  lines = [x for x in [y.strip() for y in log.split('\n')] if x != '']
  for line in lines:
    matched = [x for x in ignore_from_stderr if x.match(line)]
    if len(matched) == 0:
      logger.info('The line in the log that is not allowed: \'{}\''.format(
        line
      ))
      return True
  return False

def run_verify_postgres_db_restore(ctx, params):
  cluster_ctx = None
  try:
    part = params.get('part')
    if part is None:
      return step_failed(ctx, 'Missing \'part\' entry in params')
    file = params.get('file')
    if file is None:
      return step_failed(ctx, 'Missing \'file\' entry in params')
    if not is_path_short(part):
      return step_failed(ctx, 'Invalid part \'{}\''.format(part))
    if not is_path_safe(file):
      return step_failed(ctx, 'Invlaid file \'{}\''.format(file))
    step_info = get_step_info(ctx)
    if step_info is None:
      raise Exception('Could not get info for the current step')
    sql_path = os.path.join('/parts', part, file)
    services = {
      'postgres': {
        'image': 'slavat2018/backup-proof-pg12:0.1.0',
        'dirs': ['/var/lib/postgresql/data'],
        'environment': {
          'POSTGRES_PASSWORD': 'abc123'
      }
    }}
    cluster_ctx = create_step_cluster(ctx, services)
    if not cluster_ctx.get('success'):
      return step_failed(ctx, 'Creating cluster for \'{}\' failed'.format(
        ctx['step_dir']
      ))

    command = [
      '/bin/bash',
      '-c',
      (
        'echo "SELECT 1;" | '
        '/sbin/runuser -u postgres /usr/bin/psql'
      )
    ]
    if not wait_for_success(cluster_ctx, 'postgres', command):
      return step_failed(
        ctx,
        'Waiting for postgres to be ready failed for \'{}\''.format(
          ctx['step_dir']
        )
      )

    command = [
      '/bin/bash',
      '-c',
      (
        'cat "{}" | /sbin/runuser -u postgres /usr/bin/psql'
      ).format(sql_path)
    ]
    return_code, _, stderr = exec_in_cluster(cluster_ctx, 'postgres', command)
    if return_code != 0 or log_has_error(stderr):
      return step_failed(
        ctx,
        'Restoring database failed. Retcode: {}. Error log:\n\'{}\'\n'.format(
          return_code,
          stderr
        )
      )
    return step_success(ctx)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error(
      'Verifying postgres db restore failed \'{}\' failed: {}'.format(
        ctx['step'],
        ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
      )
    )
    return step_failed(ctx)
  finally:
    destroy_cluster(cluster_ctx)

