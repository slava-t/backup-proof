import datetime
import os
import glob

from backup_confirm.logger import get_logger
from backup_confirm.step import step_success, step_failed

DEFAULT_HOURS = 24 * 7
logger = get_logger('verify_no_old_files')

def run_verify_no_old_files(ctx, params):
  part = params.get('part')
  if part is None:
    return step_failed(ctx, 'Missing \'part\' entry in params')
  glob_param = params.get('glob')
  if glob_param is None:
    return step_failed(ctx, 'Missing \'glob\' entry in params')
  hours_str = str(params.get('hours') or DEFAULT_HOURS).strip()
  if not hours_str.isdigit() or int(hours_str) == 0:
    return step_failed(
      ctx,
      'The \'hours\' entry is expected to be a positive integer'
    )
  seconds = int(hours_str) * 3600
  full_glob = os.path.join(ctx['parts_dir'], part, glob_param)
  paths = glob.glob(full_glob)
  for p in paths:
    mod_time = os.stat(p).st_mtime
    now = datetime.datetime.now().timestamp()
    if now - mod_time > seconds:
      step_failed(
        ctx,
        'The file \'{}\' is older than {} hours.'. format(p, hours_str)
      )
  step_success(ctx)

