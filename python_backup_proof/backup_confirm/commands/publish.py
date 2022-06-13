from backup_confirm.logger import get_logger
from backup_confirm.step import step_success
from backup_confirm.pack import pack_parts, prune_parts
from backup_confirm.paths import PUBLISH_DIR

PACKS_TO_KEEP = 3

logger = get_logger('publish command')

def run_publish(ctx, _):
  logger.info('Publishing to directory \'{}\''.format(PUBLISH_DIR))
  pack_parts(ctx, PUBLISH_DIR, gz=True)
  logger.info('Prunning published packs in \'{}\''.format(PUBLISH_DIR))
  prune_parts(PUBLISH_DIR, keep=PACKS_TO_KEEP)
  step_success(ctx)

