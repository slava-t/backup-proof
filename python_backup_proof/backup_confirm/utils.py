from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import traceback
import yaml

from backup_confirm.logger import get_logger

ARCHIVE_NAME_PARTS=4
PROCESS_NAME_PARTS=5
PACK_NAME_PARTS=4
ARCHIVE_ID_REGEX=re.compile('^[0-9]{23}$')
FID_REGEX=re.compile('^[0-9]{8}-[0-9]{6}-[0-9]{9}$')
PACK_SUFFIX_REGEX = re.compile('^([0-9]{8}-[0-9]{6}-[0-9]{9})[.]\\S*$')
NAME_REGEX=re.compile('^[a-z](_?[a-z0-9]+)*$')
SPACE_SIZE_REGEX = re.compile('^\\s*([0-9]+)\\s*([kKmMgGTt])?\\s*$')

size_multipliers = {
  'k': 1000,
  'K': 1024,
  'm': 1000**2,
  'M': 1024**2,
  'g': 1000**3,
  'G': 1024**3,
  't': 1000**4,
  'T': 1024**4
}

logger = get_logger('utils')

def is_fid(fid):
  return FID_REGEX.match(fid) is not None

def id2fid(id):
  return '{}-{}-{}'.format(id[:8], id[8:14], id[14:])

def fid2id(fid):
  return ''.join(fid.split('-'))

def get_part_archive(backup_id, part):
  prod, env, date, time, nano = backup_id.split('-')
  return '{}-{}-{}-{}{}{}'.format(
    prod,
    env,
    part,
    date,
    time,
    nano
  )

def extract_datetime(archive_id):
  year = int(archive_id[0:4])
  month = int(archive_id[4:6])
  day = int(archive_id[6:8])
  hour = int(archive_id[8:10])
  minute = int(archive_id[10:12])
  second = int(archive_id[12:14])
  ms = int(archive_id[14:20])
  return datetime(year, month, day, hour, minute, second, ms, timezone.utc)


def parse_archive_name(name):
  parts = name.split('-')
  if (len(parts) == ARCHIVE_NAME_PARTS and
    NAME_REGEX.match(parts[0]) and
    NAME_REGEX.match(parts[1]) and
    NAME_REGEX.match(parts[2]) and
    ARCHIVE_ID_REGEX.match(parts[3])):
    id = parts[3]
    return {
      'time': extract_datetime(parts[3]),
      'orig': name,
      'id': id,
      'fid': id2fid(id),
      'prod': parts[0],
      'env': parts[1],
      'part': parts[2],
    }

def parse_process_name(name):
  parts = name.split('-')
  if len(parts) == PROCESS_NAME_PARTS:
    archive_name = '{}-{}-{}'.format(
      '-'.join(parts[:2]),
      'part',
      ''.join(parts[2:])
    )
    parsed = parse_archive_name(archive_name)
    if parsed is not None:
      parsed['orig'] = name
      return parsed

def parse_packed_part_name(name):
  components = name.split('-')
  if len(components) == PACK_NAME_PARTS:
    part = components[0]
    pack_suffix = '-'.join(components[1:])
    pack_suffix_match = PACK_SUFFIX_REGEX.match(pack_suffix)
    if pack_suffix_match is not None:
      fid = pack_suffix_match.group(1)
      if NAME_REGEX.match(part):
        return {
          'orig': name,
          'part': part,
          'pack_suffex': pack_suffix,
          'fid': fid,
          'id': fid2id(fid)
        }

def parse_borg_list(borg_list_output):
  result = []
  borg_list=borg_list_output.decode('utf8').split('\n')
  for archive_name in borg_list:
    parsed = parse_archive_name(archive_name)
    if parsed:
      result.append(parsed)
  return result

def parse_space_size(size_str):
  match = SPACE_SIZE_REGEX.match(size_str)
  if match is None:
    return None
  if match.lastindex == 1:
    return int(match.group(1))
  multiplier = size_multipliers.get(match.group(2))
  if multiplier is None:
    return None
  return int(match.group(1)) * multiplier

def write_to_yaml_file(data, yaml_path):
  with open(yaml_path, 'w') as stream:
    yaml.dump(data, stream)

def read_from_yaml_file(yaml_path):
  with open(yaml_path, 'r') as stream:
    return yaml.safe_load(stream)

def get_yaml(yaml_path, default_value = None):
  try:
    return read_from_yaml_file(yaml_path)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Getting yaml error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))
  return default_value


def split_prod_env_id(prod_env_id):
  id_parts = prod_env_id.split('-')
  return ('-'.join(id_parts[:-1]), id_parts[-1])

def is_path_safe(path):
  parts = Path(path).parts
  return '..' not in parts and '.' not in parts

def is_path_short(path):
  return is_path_safe(path) and len(Path(path).parts) == 1

