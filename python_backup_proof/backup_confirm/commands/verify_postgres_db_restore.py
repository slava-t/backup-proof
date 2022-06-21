import os
import sys
import traceback

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

logger = get_logger('verify_mysql_db_restore')

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
        'image': 'mysql:5.7',
        'resources': [
          {
            'id': 'mysql-big-packet-confd',
            'path': '/etc/mysql/conf.d'
          }
        ],
        'dirs': ['/var/lib/mysql'],
        'environment': {
          'MYSQL_ROOT_PASSWORD': 'abc123'
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
        'MYSQL_PWD=abc123 /usr/bin/mysql -u root'
      )
    ]
    if not wait_for_success(cluster_ctx, 'mysql', command):
      return step_failed(
        ctx,
        'Waiting for mysql to be ready failed for \'{}\''.format(
          ctx['step_dir']
        )
      )

    command = [
      '/bin/bash',
      '-c',
      (
        'cat "{}" | MYSQL_PWD=abc123 /usr/bin/mysql -u root'
      ).format(sql_path)
    ]
    return_code, _, stderr = exec_in_cluster(cluster_ctx, 'mysql', command)
    if return_code != 0 or stderr.strip() != '':
      return step_failed(
        ctx,
        'Restoring database failed. Retcode: {}. Error: \'{}\''.format(
          return_code,
          stderr.strip()
        )
      )
    return step_success(ctx)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Verifying mysql db restore failed \'{}\' failed: {}'.format(
      ctx['step'],
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
  finally:
    destroy_cluster(cluster_ctx)

