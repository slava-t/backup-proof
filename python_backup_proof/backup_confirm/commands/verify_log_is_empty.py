import os
import subprocess

from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import is_path_safe

def run_verify_log_is_empty(ctx, params):
  log_file = params.get('file')
  if log_file is None:
    return step_failed(ctx, 'Missing \'file\' in params')
  if not is_path_safe(log_file):
    return step_failed(ctx, 'Invalid filename: \'{}\''.format(log_file))
  log_path = os.path.join(ctx['parts_dir'], 'logs', log_file)
  if not os.path.exists(log_path):
    return step_failed(ctx, 'Log file \'{}\' does not exist.'.format(log_path))

  result = subprocess.run(
    [
      '/bin/bash',
      '-c',
      'cat "{}" | /usr/local/bin/verify_is_empty'.format(log_path)
    ]
  )
  if result.returncode != 0:
    return step_failed(
      ctx,
      'Log file \'{}\' is not empty. Return code: {}'.format(
        log_path,
        result.returncode
      )
    )
  step_success(ctx)

