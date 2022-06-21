import os

from backup_confirm.commands.create_confirm_steps_yaml import (
  run_create_confirm_steps_yaml
)
from backup_confirm.commands.extract_part import run_extract_part_command
from backup_confirm.commands.star import run_star_command
from backup_confirm.commands.check_borg_data import run_check_borg_data
from backup_confirm.commands.clean_borg_repo import run_clean_borg_repo
from backup_confirm.commands.mark_verified_in_borg import (
  run_mark_verified_in_borg
)
from backup_confirm.commands.publish import run_publish
from backup_confirm.commands.release import run_release
from backup_confirm.commands.verify_backup_log import run_verify_backup_log
from backup_confirm.commands.verify_borg_log import run_verify_borg_log
from backup_confirm.commands.verify_log_is_empty import run_verify_log_is_empty
from backup_confirm.commands.verify_mysql_db_restore import (
  run_verify_mysql_db_restore
)
from backup_confirm.commands.verify_part_min_size import (
  run_verify_part_min_size
)
from backup_confirm.commands.verify_postgres_db_restore import (
  run_verify_postgres_db_restore
)
from backup_confirm.commands.verify_preceeding_steps import (
  run_verify_preceeding_steps
)

from backup_confirm.commands.verify_sha1sum import run_verify_sha1sum
from backup_confirm.commands.verify_sql_file_sha1sum import (
  run_verify_sql_file_sha1sum
)

from backup_confirm.step import step_skipped, verify_dependencies
from backup_confirm.utils import read_from_yaml_file



commands = {
  '*': run_star_command,
  'extract_part': run_extract_part_command,
  'verify_sha1sum': run_verify_sha1sum,
  'create_confirm_steps_yaml': run_create_confirm_steps_yaml,
  'verify_part_min_size': run_verify_part_min_size,
  'verify_backup_log': run_verify_backup_log,
  'verify_borg_log': run_verify_borg_log,
  'verify_log_is_empty': run_verify_log_is_empty,
  'verify_preceeding_steps': run_verify_preceeding_steps,
  'verify_sql_file_sha1sum': run_verify_sql_file_sha1sum,
  'verify_mysql_db_restore': run_verify_mysql_db_restore,
  'verify_postgres_db_restore': run_verify_postgres_db_restore,
  'check_borg_data': run_check_borg_data,
  'mark_verified_in_borg': run_mark_verified_in_borg,
  'clean_borg_repo': run_clean_borg_repo,
  'publish': run_publish,
  'release': run_release
}

def get_command_runner(command):
  return commands.get(command)

def run_command(ctx):
  step_data = read_from_yaml_file(ctx['step'])
  command = step_data.get('command')
  params = step_data.get('params')
  dependencies = set(step_data.get('dependencies') or [])
  fail_reason = verify_dependencies(ctx, step_data.get('id'), dependencies)
  if fail_reason is not None:
    return step_skipped(ctx, fail_reason)
  command_func = get_command_runner(command)
  if command_func is not None:
    return command_func(ctx, params)
  raise Exception('Invalid command \'{}\' for step \'{}\''.format(
    command,
    ctx['step']
  ))
