from backup_confirm.borg import extract_part
from backup_confirm.logger import get_logger
from backup_confirm.step import step_success, step_failed

logger = get_logger('extract_part')
def run_extract_part_command(ctx, params):
  part = params.get('part')
  if part is None:
    return step_failed(ctx, 'Missing \'part\' in params');
  if type(part) is not str:
    return step_failed(
      ctx,
      'The value of \'part\' param is not string. Provided value: {}'.format(
        part
      )
    )
  logger.info('Extracting part \'{}\''.format(part))
  result = extract_part(ctx, part)
  if not result:
    raise Exception('Extraction part \'{}\' failed'.format(part))
  step_success(ctx)

