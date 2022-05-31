import os

from backup_confirm.borg import (prefix_archive_names)
from backup_confirm.logger import get_logger
from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import (
  get_part_archive,
  read_from_yaml_file
)

logger = get_logger('mark_verified_in_borg')

def run_mark_verified_in_borg(ctx, _):
  main_dir = ctx['main_dir']
  logger.info('Checking directory \'{}\''.format(main_dir))
  data_status = read_from_yaml_file(os.path.join(main_dir, 'data_status.yaml'))
  if data_status.get('status') == 'success':
    parts = os.listdir(ctx['parts_dir'])
    logger.info('Detected parts: {}'.format(parts))
    backup_id = os.path.split(main_dir)[1]
    logger.info('Backup ID: {}'.format(backup_id))
    archives = [get_part_archive(backup_id, x) for x in parts]
    if not prefix_archive_names('v', archives):
      return step_failed(ctx, 'Prefixing archives in borg failed')
    return step_success(ctx)
  step_failed(
    ctx,
    (
      'Marking parts as verified in borg failed '
      'because data status is not \'success\''
    )
  )

