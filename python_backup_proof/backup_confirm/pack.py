import base64
import hashlib
import hmac
import os
import subprocess
import sys
import traceback

from backup_confirm.config import get_enc_config
from backup_confirm.confirm_vars import (
  CONFIRM_PRODUCT,
  CONFIRM_ENVIRONMENT,
  CONFIRM_FID
)
from backup_confirm.logger import get_logger
from backup_confirm.utils import parse_packed_part_name

DEFAULT_PACKS_TO_KEEP = 3

logger = get_logger('pack')

def get_password(pack_pass, packname):
  m = hmac.new(bytearray(pack_pass, 'utf-8'), digestmod=hashlib.sha256)
  m.update(bytearray(packname, 'utf-8'))
  base64_digest = base64.b64encode(m.digest()).decode('utf-8')
  clean_digest = base64_digest.replace('/', 'a').replace('+', 'b').replace(
    '=',
    'c'
  )
  return clean_digest[0:24]

def pack_dir(src_dir, dest_path, password, compression=0):
  logger.info('Packing dir \'{}\' to \'{}\''.format(src_dir, dest_path))
  flags = '-cf'
  pack_command = (
    '/bin/tar {} - * | /bin/gpg --batch -o "{}" -c -z {}'.format(
      flags,
      dest_path,
      compression
  ))
  pack_auth_command = '{} --passphrase "{}"'.format(pack_command, password)
  result = subprocess.run(
    [
      '/bin/bash',
      '-c',
      pack_auth_command
    ],
    cwd=src_dir
  )
  if result.returncode != 0:
    pack_masked_command = '{} --passphrase "{}"'.format( pack_command, '****')
    raise Exception('The command {} exited with code {}'.format(
      [
        '/bin/bash',
        '-c',
        pack_masked_command,
      ],
      result.returncode
    ))

def pack_parts(ctx, dest_dir, compression=0):
  config = get_enc_config()
  pack_pass = config.get('pack_pass')
  if type(pack_pass) is not str:
    raise Exception('There is no \'pack_pass\' entry in config')

  prod_dest_dir = os.path.join(dest_dir, str(CONFIRM_PRODUCT))
  env_dest_dir = os.path.join(prod_dest_dir, str(CONFIRM_ENVIRONMENT))
  os.makedirs(env_dest_dir, mode=0o755, exist_ok=True)
  parts_dir = ctx['parts_dir']
  logger.info('Packing all parts from \'{}\' to \'{}\''.format(
    parts_dir,
    env_dest_dir
  ))
  parts = [x for x in os.listdir(parts_dir) if x not in ['logs', 'confirm']]
  logger.info('Packing parts {}'.format(parts))
  failed_parts = []
  for part in parts:
    try:
      logger.info('Packing part \'{}\''.format(part))
      packname = '{}-{}.tar.gpg'.format(
        part,
        CONFIRM_FID
      )
      password = get_password(pack_pass, packname)
      src_dir = os.path.join(parts_dir, part)
      dest_path = os.path.join(env_dest_dir, packname)
      pack_dir(src_dir, dest_path, password, compression)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      logger.error('Packing part \'{}\' error: {}'.format(part, ''.join(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
      )))
      failed_parts.append(part)
  if len(failed_parts) > 0:
    raise Exception('Error packing parts {}'.format(failed_parts))

def prune_env_parts(env_dir, keep):
  logger.info('Prunning environment dir \'{}\''.format(env_dir))
  filenames = os.listdir(env_dir)
  parts = {}
  for filename in filenames:
    pack = parse_packed_part_name(filename)
    file_path = os.path.join(env_dir, filename)
    if pack is not None and os.path.isfile(file_path):
      partname = pack['part']
      part = parts.get(partname)
      if part is None:
        part = []
        parts[partname] = part
      part.append(pack)
  for partname, packs in parts.items():
    sorted_packs = sorted(packs, key=lambda x: x['fid'], reverse=True)
    to_delete = sorted_packs[keep:]
    logger.info('Packs to remove: {}'.format([x['orig'] for x in to_delete]))
    for pack in to_delete:
      pack_path = os.path.join(env_dir, pack['orig'])
      logger.info('Deleting file: \'{}\''.format(pack_path))
      os.remove(pack_path)
      logger.info('Deleted file: \'{}\''.format(pack_path))

def prune_parts(dest_dir, keep=DEFAULT_PACKS_TO_KEEP):
  logger.info('Prunning parts in dir \'{}\''.format(dest_dir))
  env_dir = os.path.join(
    dest_dir,
    str(CONFIRM_PRODUCT),
    str(CONFIRM_ENVIRONMENT)
  )
  return prune_env_parts(env_dir, keep)

def prune_all_parts(dest_dir, keep=DEFAULT_PACKS_TO_KEEP):
  products = os.listdir(dest_dir)
  logger.info('Detected products: {}'.format(products))
  for product in products:
    prod_dir = os.path.join(dest_dir, product)
    environments = os.listdir(prod_dir)
    for environment in environments:
      env_dir = os.path.join(prod_dir, environment)
      prune_env_parts(env_dir, keep)


