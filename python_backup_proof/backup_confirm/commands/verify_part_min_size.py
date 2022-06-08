import os
import subprocess

from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import parse_space_size
from backup_confirm.logger import get_logger

logger = get_logger('verify_part_min_size')


DEFAULT_MIN_SIZE = '1M'

def run_verify_part_min_size(ctx, params):
  part = params.get('part')
  size_str = params.get('size') or DEFAULT_MIN_SIZE
  if part is None:
    raise Exception('Verify sha1sum expects \'part\' in params')
  size = parse_space_size(size_str)
  logger.info('Verifying part \'{}\' to have at least \'{}\' bytes.'.format(
    part,
    size
  ))
  if size is None:
    raise Exception('Invalid size: \'{}\''.format(size_str))
  part_dir = os.path.join(ctx['parts_dir'], part)
  result = subprocess.run(
    [
      'du',
      '--apparent-size',
      '-sb'
    ],
    check=True,
    capture_output=True,
    text=True,
    cwd=part_dir
  )
  du_words = result.stdout.split()
  if len(du_words) < 2:
    raise Exception('Not enough components from \'du\' output: {}'.format(
      du_words
    ))
  du_size_str = du_words[0]
  if not du_size_str.isdigit():
    raise Exception('Unexpected size from \'du\' output: {}'.format(
      du_words
    ))
  du_size = int(du_size_str)
  logger.info(
    'part: \'{}\', real size: {}, expected minimal size: {}'.format(
      part,
      du_size,
      size
    )
  )
  if int(du_size) < size:
    return step_failed(
      ctx,
      'The real size is {}. The expected minimal size is {}'.format(
        du_size, size
      )
    )
  step_success(ctx)

