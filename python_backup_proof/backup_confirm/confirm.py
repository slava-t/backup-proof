import sys
import time
import traceback

from backup_confirm.borg import (
  get_latest_parts,
  get_borg_credentials,
  create_repo
)

from backup_confirm.config import get_enc_config, reset_enc_config
from backup_confirm.logger import get_logger
from backup_confirm.process import create_processes

SCAN_AND_PROCESS_INTERVAL = 180 #3 minutes interval

INITIAL_WAITING = 10
RESET_ENC_CONFIG_INTERVAL = 300 #5 minutes interval

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

def try_create_repos():
  try:
    reset_enc_config()
    enc_config = get_enc_config()
    repos = enc_config.get('repos') or {}
    for _, repo in repos.items():
      products = repo.get('products') or {}
      for product_name, product in products.items():
        environments = product.get('environments') or {}
        for environment_id in environments:
          logger.info(
            f'Trying to create repo for {product_name!r} in '
            f'{environment_id!r} environment'
          )
          repo_ref, rsh, password = get_borg_credentials(
            repo,
            product_name,
            environment_id
          )
          create_repo(rsh, repo_ref, password)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in confirm try_create_repos function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))

def scan_and_process():
  try:
    reset_enc_config()
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
    time.sleep(INITIAL_WAITING)
    try_create_repos()
    while True:
      scan_and_process()
      time.sleep(SCAN_AND_PROCESS_INTERVAL)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Error in confirm main function: {}'.format(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))
