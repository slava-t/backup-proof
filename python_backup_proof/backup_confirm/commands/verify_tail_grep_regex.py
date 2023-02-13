import os
import subprocess

from backup_confirm.logger import get_logger
from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import is_path_short, is_path_safe

DEFAULT_LINES = '10'
GREP_PATH = '/usr/bin/grep'

logger = get_logger('verify_end_matches_regex')

def run_verify_tail_grep_regex(ctx, params):
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

  lines_str = str(params.get('lines') or DEFAULT_LINES).strip()
  if not lines_str.isdigit() or int(lines_str) == 0:
    return step_failed(
      ctx,
      'The \'lines\' entry is expected to be a positive integer'
    )

  regex = params.get('regex')
  if regex is None:
    return step_failed(ctx, 'Missing \'regex\' entry in params')
  negate = bool(params.get('negate')) or False;

  prefix = '! ' if negate else ''
  command = '{}tail -n {} "{}" | {} -E -- \'{}\''.format(
    prefix,
    lines_str,
    file_path,
    GREP_PATH,
    regex
  )

  logger.info(
    'Verify tail grep regex completed with command: {}'.format(command)
  )
  result = subprocess.run(
    [
      '/bin/bash',
      '-c',
      command
    ]
  )
  if result.returncode != 0:
    return step_failed(
      ctx,
      'Tail {} lines and grep regex \'{}\' failed. Command: {}'.format(
        lines_str,
        regex,
        command
      )
    )
  step_success(ctx)

