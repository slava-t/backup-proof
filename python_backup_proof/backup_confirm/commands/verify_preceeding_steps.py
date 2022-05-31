import os
import sys
import traceback

from backup_confirm.step import (
  get_step_info,
  step_success,
  step_failed,
  verify_dependencies
)
from backup_confirm.utils import (
  is_path_short,
  write_to_yaml_file
)
from backup_confirm.logger import get_logger

logger = get_logger('verify_preceeding_steps')

def set_verified_status(ctx, status_file, fail_reason = None):
  try:
    if not status_file:
      return
    status_path = os.path.join(ctx['main_dir'], status_file)
    status_content = {
      'status': 'success'
    }
    if fail_reason is not None:
      status_content = {
        'status': 'failed',
        'reason': 'reason'
      }

    write_to_yaml_file( status_content, status_path)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Processing error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))

def run_verify_preceeding_steps(ctx, params):
  status_file = None
  try:
    step_info = get_step_info(ctx)
    status_file = params.get('status')
    if status_file and not is_path_short(status_file):
      return step_failed(ctx, 'Invalid file name \'{}\''.format(status_file))
    fail_reason = verify_dependencies(ctx, step_info['id'])
    set_verified_status(ctx, status_file, fail_reason)
    if fail_reason is not None:
      logger.info('Failed reason: {}'.format(fail_reason))
      return step_failed(ctx, fail_reason)
    step_success(ctx)
  except Exception as e:
    set_verified_status(ctx, status_file, str(e))
    raise e
