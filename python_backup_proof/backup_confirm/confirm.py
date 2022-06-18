import sys
import time
import traceback

from backup_confirm.borg import get_latest_parts, get_borg_credentials
from backup_confirm.config import get_enc_config
from backup_confirm.logger import get_logger
from backup_confirm.process import create_processes

SCAN_AND_PROCESS_INTERVAL = 180 #3 minutes interval

ARCHIVE_MAX_AGE = 12 * 3600 #12 hours

logger = get_logger('confirm')

logger.info('Starting confirm script')


def process_product(repo_name, repo, product_name, environment_id):
  try:
    repo_ref, rsh, password = get_borg_credentials(
      repo,
      product_name,
      environment_id
    )
    latest_parts = get_latest_parts(
      rsh,
      repo_ref,
      password,
      maxAgeInSeconds=ARCHIVE_MAX_AGE
    ) or {}
    create_processes(repo_name, repo, latest_parts)


  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error(
      'Processing error \'{}\' in environment \'{}\' failed: {}'.format(
        product_name,
        environment_id,
        ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
      )
    )

def scan_and_process():
  try:
    enc_config = get_enc_config()
    repos = enc_config.get('repos') or {}
    for repo_name, repo in repos.items():
      products = repo.get('products') or {}
      for product_name, product in products.items():
        environments = product.get('environments') or {}
        for environment_id in environments:
          process_product(
            repo_name,
            repo,
            product_name,
            environment_id,
          )
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in confirm scan_and_process function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))



def main():
  try:
    while True:
      scan_and_process()
      time.sleep(SCAN_AND_PROCESS_INTERVAL)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in confirm main function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
