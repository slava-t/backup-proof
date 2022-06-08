import os

from backup_confirm.borg import (
  get_borg_archive_names,
  delete_borg_archives
)

from backup_confirm.step import step_success, step_failed
from backup_confirm.utils import (
  parse_archive_name
)
VERIFIED_PREFIX = 'v-'
MAX_VERIFIED = 3
MAX_UNVERIFIED = 3

def run_clean_borg_repo(ctx, _):
  archives = list(reversed(get_borg_archive_names()))
  to_delete = []
  known_parts = {}
  for archive in archives:
    name = archive
    is_verified = False
    if archive.startswith(VERIFIED_PREFIX):
      is_verified = True
      name = archive[len(VERIFIED_PREFIX):]

    parsed = parse_archive_name(name)
    if parsed is None:
      to_delete.append(archive)
      continue

    part = '{}-{}-{}'.format(parsed['prod'], parsed['env'], parsed['part'])
    known_part = known_parts.get(part)
    if known_part is None:
      known_part = {
        'v': [],
        'u': []
      }
      known_parts[part] = known_part

    verified = known_part['v']
    unverified = known_part['u']
    if is_verified:
      if len(verified) < MAX_VERIFIED:
        verified.append(archive)
      else:
        to_delete.append(archive)
    else:
      if len(verified) == 0 and len(unverified) < MAX_UNVERIFIED:
        unverified.append(archive)
      else:
        to_delete.append(archive)
  if delete_borg_archives(to_delete):
    return step_success(ctx)
  return step_failed(ctx, 'Borg repo cleaning failed')
