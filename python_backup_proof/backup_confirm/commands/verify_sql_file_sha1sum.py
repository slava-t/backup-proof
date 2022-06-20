import os
import subprocess

from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import is_path_short, is_path_safe

def run_verify_sql_file_sha1sum(ctx, params):
  part = params.get('part')
  if part is None:
    return step_failed(ctx, 'Missing \'part\' entry in params')
  file = params.get('file')
  if file is None:
    return step_failed(ctx, 'Missing \'file\' entry in params')
  if not is_path_short(part):
    return step_failed(ctx, 'Invalid part \'{}\''.format(part))
  if not is_path_safe(file):
    return step_failed(ctx, 'Invalid filename file \'{}\''.format(file))
  file_path = os.path.join(ctx['parts_dir'], part, file)
  if not os.path.exists(file_path):
    return step_failed(ctx, 'File does not exist: \'{}\''.format(file_path))
  result = subprocess.run(
    [
      '/bin/bash',
      '-c',
      'cat "{}" | /usr/local/bin/verify_embedded_sha1sum'.format(file_path)
    ]
  )
  if result.returncode != 0:
    return step_failed(ctx, 'SQL file sha1sum verification failed')
  step_success(ctx)

