import os
import sys
from backup_confirm.config import get_enc_config
from backup_confirm.borg import get_latest_parts
from backup_confirm.logger import get_logger
from backup_confirm.process import create_processes


STATE_DIR='/confirm-state'

logger = get_logger('confirm')

logger.info('Starting confirm script')


def process_product(repo, product_name, product, environment_id, environment):
  try:
    repo_ref = os.path.join(repo.get('repo', ''), environment.get('repo', ''))
    rsh = environment.get('rsh', repo.get('rsh'))
    password = environment.get('pass', '')
    latest_parts = get_latest_parts(
      rsh,
      repo_ref,
      password
    ) or {}
    create_processes(latest_parts)


  except Exception as e:
    logger.error('Backup confirmation proces for {} in {} failed: {}'.format(
      product_name,
      environment_id,
      e
    ))
    exc_type, exc_value = sys.exc_info()[:2]
    logger.info('exception type: {}'.format(exc_type))
    logger.info('exception value: {}'.format(exc_value))

def main():
  try:
    #config = load_config(CONFIG_PATH)
    enc_config = get_enc_config()
    repos = enc_config.get('repos') or {}
    for _, repo in repos.items():
      products = repo.get('products') or {}
      for product_name, product in products.items():
        environments = product.get('environments') or {}
        for environment_id, environment in environments.items():
          process_product(
            repo,
            product_name,
            product,
            environment_id,
            environment
          )
  except Exception as e:
    logger.error('Backup confirmation process failed: {}'.format(e))
    exc_type, exc_value = sys.exc_info()[:2]
    logger.info('exception type: {}'.format(exc_type))
    logger.info('exception_value: {}'.format(exc_value))



