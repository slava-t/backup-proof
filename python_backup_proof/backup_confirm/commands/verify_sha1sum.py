import os
import subprocess
from backup_confirm.step import step_success, step_failed

def run_verify_sha1sum(ctx, params):
  part = params.get('part')
  if part is None:
    raise Exception('Verify sha1sum expects \'part\' in params')
  part_dir = os.path.join(ctx['parts_dir'], part)
  sha1sum_path = os.path.join(part_dir, 'sha1sum')
  result = subprocess.run(
    [
      '/usr/bin/sha1sum',
      '-c',
      sha1sum_path
    ],
    cwd=part_dir
  )
  if result.returncode != 0:
    return step_failed('Part sha1sum verification failed')
  step_success(ctx)
