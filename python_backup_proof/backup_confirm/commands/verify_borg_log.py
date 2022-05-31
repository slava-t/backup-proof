import os
import subprocess
from backup_confirm.step import step_success
from backup_confirm.confirm_vars import CONFIRM_ZONE

def run_verify_borg_log(ctx, params):
  part = params.get('part')
  if part is None:
    raise Exception('Verify borg log expects \'part\' in params')
  log_file = '{}-{}.log'.format(CONFIRM_ZONE, part)
  log_path = os.path.join(ctx['parts_dir'], 'logs/log', log_file)
  subprocess.run(
    [
      'bash',
      '-c',
      'cat \'{}\' | /usr/local/bin/verify_borg_log'.format(log_path)
    ],
    check=True
  )
  step_success(ctx)
