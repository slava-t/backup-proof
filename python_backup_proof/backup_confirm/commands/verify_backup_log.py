import os
import subprocess

from backup_confirm.confirm_vars import CONFIRM_ZONE, CONFIRM_TIMESTAMP_ID
from backup_confirm.step import step_success

def run_verify_backup_log(ctx, params):
  log_file = (params or {}).get('file') or 'backup.log'

  if '/' in log_file:
    raise Exception('Verify \'file\' cannot contain \'/\'')
  log_path = os.path.join(ctx['parts_dir'], 'logs/log', log_file)
  command = (
    'cat \'{}\' | BACKUP_ZONE=\'{}\' BACKUP_ID=\'{}\' '
    '/usr/local/bin/verify_backup_log'
  ).format(log_path, CONFIRM_ZONE, CONFIRM_TIMESTAMP_ID)
  subprocess.run(
    [
      'bash',
      '-c',
      command
    ],
    check=True
  )
  step_success(ctx)
