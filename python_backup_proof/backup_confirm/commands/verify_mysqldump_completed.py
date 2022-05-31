import os
import subprocess

from backup_confirm.logger import get_logger
from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import is_path_short, is_path_safe

logger = get_logger('verify_mysqldump_completed')

def run_verify_mysqldump_completed(ctx, params):
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
  command = 'tail -n 2 "{}" | /usr/bin/grep -E -- \'{}\''.format(
    file_path,
    (
      '^-- Dump completed on '
      '[0-9]{4}(-[0-9]{2}){2}\\s+[0-9]{1,2}(:[0-9]{2}){2}$'
    )
  )
  logger.info('Verify mysqldump completed with command: {}'.format(command))
  result = subprocess.run(
    [
      '/bin/bash',
      '-c',
      command
    ]
  )
  if result.returncode != 0:
    return step_failed(ctx, 'Could not find mysqldump \'{}\' signature'.format(
      '-- Dump completed on ...'
    ))
  step_success(ctx)
