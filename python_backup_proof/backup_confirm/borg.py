import os
import re
from shutil import rmtree
from datetime import datetime, timezone
import subprocess
import sys
import traceback

from backup_confirm.config import get_enc_config
from backup_confirm.confirm_vars import (
  CONFIRM_REPO_NAME,
  CONFIRM_PRODUCT,
  CONFIRM_ENVIRONMENT,
  CONFIRM_TIMESTAMP_ID
)

from backup_confirm.logger import get_logger
from backup_confirm.utils import parse_borg_list, id2fid

BORG_PASSPHRASE_REGEX=re.compile('BORG_PASSPHRASE=\'[a-zA-Z0-9]*\'')

logger = get_logger('borg')

def log_borg_exception(exc_type, exc_value , tb):
  error = clean_borg_error(exc_value)
  logger.error('Error: {}'.format(''.join(traceback.format_exception(
    exc_type,
    Exception(error),
    tb
  ))))

def get_borg_credentials(repo, product_name, environment_id):
  products = repo.get('products') or {}
  product = products.get(product_name) or {}
  environments = product.get('environments') or {}
  environment = environments.get(environment_id) or {}
  repo_ref = os.path.join(repo.get('repo', ''), environment.get('repo', ''))
  rsh = environment.get('rsh', repo.get('rsh'))
  password = environment.get('pass', '')
  return (repo_ref, rsh, password)


def get_config_borg_credentials():
  config = get_enc_config()
  repos = config.get('repos') or {}
  repo = repos.get(CONFIRM_REPO_NAME) or {}
  return get_borg_credentials(repo, CONFIRM_PRODUCT, CONFIRM_ENVIRONMENT)

def get_borg_list(rsh, repo, password):
  try:
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo,
      password,
      '/usr/local/bin/borg list --short'
    )
    result = subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command,
      ],
      check=True,
      capture_output=True
    )
    return parse_borg_list(result.stdout)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
    return []

def get_borg_archive_names():
  try:
    repo, rsh, password = get_config_borg_credentials();
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo,
      password,
      '/usr/local/bin/borg list --short --lock-wait 20'
    )
    res = subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command,
      ],
      check=True,
      capture_output=True
    )
    return res.stdout.decode('utf8').split('\n')
  except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
    raise e

def delete_borg_archives(archives):
  try:
    if archives is None or len(archives) == 0:
      return True
    repo, rsh, password = get_config_borg_credentials();
    borg_command = (
      '/usr/local/bin/borg delete --lock-wait 20 --save-space ::{}'
    ).format(' '.join(archives))
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo,
      password,
      borg_command
    )
    subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command,
      ],
      check=True
    )
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
  return False

def extract_part(ctx, part):
  try:
    parts_dir = ctx.get('parts_dir')
    part_dir = os.path.join(parts_dir, part)
    if os.path.isdir(part_dir):
      rmtree(part_dir)
    os.makedirs(part_dir, mode=0o660, exist_ok=True)
    repo_ref, rsh, password = get_config_borg_credentials();
    archive_id = '{}-{}-{}-{}'.format(
      CONFIRM_PRODUCT,
      CONFIRM_ENVIRONMENT,
      part,
      CONFIRM_TIMESTAMP_ID
    )
    borg_command = '/usr/local/bin/borg extract --lock-wait 20 ::{}'.format(
      archive_id
    )
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo_ref,
      password,
      borg_command
    )
    subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command
      ],
      check=True,
      cwd=part_dir
    )
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
  return False

def check_borg_data():
  try:
    repo_ref, rsh, password = get_config_borg_credentials();
    borg_command = '/usr/local/bin/borg check --lock-wait 20 --verify-data'
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo_ref,
      password,
      borg_command
    )
    subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command
      ],
      check=True,
    )
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
  return False

def prefix_archive_name(rsh, repo, password, prefix, archive):
  try:
    logger.info('Prefixing archive: {}'.format(archive))
    borg_command = (
      '/usr/local/bin/borg rename --lock-wait 20 "::{}" "{}-{}"'
    ).format(archive, prefix, archive)
    borg_bash_command = get_borg_bash_command(
      rsh,
      repo,
      password,
      borg_command
    )
    subprocess.run(
      [
        '/bin/bash',
        '-c',
        borg_bash_command
      ],
      check=True,
    )
    return True
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
  return False

def prefix_archive_names(prefix, archives):
  try:
    repo_ref, rsh, password = get_config_borg_credentials();
    success = True
    for archive in archives:
      success = success and prefix_archive_name(
        rsh,
        repo_ref,
        password,
        prefix,
        archive
      )
    return success
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)
  return False

def get_latest_parts(rsh, repo, password, maxAgeInSeconds=3600*24):
  try:
    borg_list = list(reversed(get_borg_list(rsh, repo, password)))
    #logger.info('borg_list={}'.format(borg_list))
    confirm_map = {}
    for borg_item in borg_list:
      ageInSeconds = (
        datetime.now(timezone.utc) - borg_item.get('time', datetime.min)
      ).total_seconds()
      if borg_item.get('part') == 'confirm' and ageInSeconds <= maxAgeInSeconds:
        prod_env_id = '{}-{}'.format(
          borg_item.get('prod', ''), borg_item.get('env', '')
        )
        if prod_env_id not in confirm_map:
          confirm_map[prod_env_id] = borg_item

    result = {}
    for prod_env_id, confirm_part in confirm_map.items():
      parts = {}
      for borg_item in borg_list:
        if (
          confirm_part.get('id') == borg_item.get('id') and
          confirm_part.get('env') == borg_item.get('env') and
          confirm_part.get('prod') == borg_item.get('prod')
        ):
          parts[borg_item.get('part')] = borg_item
      result[prod_env_id] = parts
    return result
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_borg_exception(exc_type, exc_value, exc_traceback)


def get_borg_bash_command(rsh, repo, password, command):
  return (
    'BORG_RELOCATED_REPO_ACCESS_IS_OK=yes '
    'BORG_RSH=\'{}\' '
    'BORG_PASSPHRASE=\'{}\' '
    'BORG_REPO=\'{}\' {}'
  ).format(
    rsh,
    password,
    repo,
    command
  )

def clean_borg_error(error):
  return BORG_PASSPHRASE_REGEX.sub('BORG_PASSPHRASE=\'masked\'', str(error) or '')

