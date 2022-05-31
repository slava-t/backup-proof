import re
from datetime import datetime, timezone
import subprocess

from backup_confirm.logger import get_logger
from backup_confirm.utils import extract_datetime

ARCHIVE_NAME_PARTS=4
NAME_REGEX=re.compile('^[a-z](_?[a-z0-9]+)*$')
ARCHIVE_ID_REGEX=re.compile('^[0-9]{23}$')
BORG_PASSPHRASE_REGEX=re.compile('BORG_PASSPHRASE=\'[a-zA-Z0-9]*\'')

logger = get_logger('borg')

def parse_borg_list(borg_list_output):
  result = []
  borg_list=borg_list_output.decode('utf8').split('\n')
  for archive_name in borg_list:
    parts = archive_name.split('-')
    if (len(parts) == ARCHIVE_NAME_PARTS and
      NAME_REGEX.match(parts[0]) and
      NAME_REGEX.match(parts[1]) and
      NAME_REGEX.match(parts[2]) and
      ARCHIVE_ID_REGEX.match(parts[3])):
      result.append({
        'time': extract_datetime(parts[3]),
        'orig': archive_name,
        'id': parts[3],
        'prod': parts[0],
        'env': parts[1],
        'part': parts[2],
      })
  return result

def log_borg_error(e):
  error = clean_borg_error(
    'Error: Getting borg list error.{}'.format(e)
  )
  logger.error(error)


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
      'bash',
      '-c',
      borg_bash_command,
      ],
      check=True,
      capture_output=True
    )
    return parse_borg_list(result.stdout)
  except Exception as e:
    log_borg_error(e)
    return []

def get_latest_parts(rsh, repo, password, maxAgeInSeconds=3600*24):
  try:
    borg_list = list(reversed(get_borg_list(rsh, repo, password)))
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
  except Exception as e:
    log_borg_error(e)


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
  return BORG_PASSPHRASE_REGEX.sub('BORG_PASSPHRASE=\'masked\'', error or '')

