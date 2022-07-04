from backup_confirm.logger import get_logger
from backup_confirm.pack import pack_parts, prune_parts
from backup_confirm.paths import RELEASE_DIR
from backup_confirm.step import step_success

PACKS_TO_KEEP = 5

logger = get_logger('release command')

def run_release(ctx, _):
  logger.info('Releasing to directory \'{}\''.format(RELEASE_DIR))
  pack_parts(ctx, RELEASE_DIR, compression=1)
  logger.info('Prunning releases in \'{}\''.format(RELEASE_DIR))
  prune_parts(RELEASE_DIR, keep=PACKS_TO_KEEP)
  step_success(ctx)


