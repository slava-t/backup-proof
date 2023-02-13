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
from backup_confirm.commands.set_options import run_set_options
from backup_confirm.commands.verify_backup_log import run_verify_backup_log
from backup_confirm.commands.verify_borg_log import run_verify_borg_log
from backup_confirm.commands.verify_log_is_empty import run_verify_log_is_empty
from backup_confirm.commands.verify_mysql_db_restore import (
  run_verify_mysql_db_restore
)
from backup_confirm.commands.verify_mysqldump_completed import (
  run_verify_mysqldump_completed
)
from backup_confirm.commands.verify_part_min_size import (
  run_verify_part_min_size
)
from backup_confirm.commands.verify_pg_dumpall_completed import(
  run_verify_pg_dumpall_completed
)
from backup_confirm.commands.verify_tail_grep_regex import (
  run_verify_tail_grep_regex
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
from backup_confirm.logger import get_logger

from backup_confirm.step import (
  step_skipped,
  verify_dependencies,
  step_success
)

from backup_confirm.utils import read_from_yaml_file, get_yaml

logger = get_logger('command_runner')

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
  'release': run_release,
  'set_options': run_set_options,
  'verify_mysqldump_completed': run_verify_mysqldump_completed,
  'verify_pg_dumpall_completed': run_verify_pg_dumpall_completed,
  'verify_tail_grep_regex': run_verify_tail_grep_regex
}

def get_command_runner(command):
  return commands.get(command)

def get_option_params(step_options, options):
  logger.info('Calling get_option_params: step_options={}, options={}'.format(
    step_options,
    options
  ))
  result = {}
  for step_option in step_options:
    name = step_option.get('name')
    if name is None:
      raise Exception('Missing \'name\' entry in step options: {}'.format(
        step_option
      ))
    param_name = step_option.get('param') or name
    option = options.get(name)
    if option is None:
      default_value = step_option.get('default')
      if default_value is not None:
        result[param_name] = step_option.get('default')
    else:
      result[param_name] = option
  logger.info('Returning from get_option_params: {}'.format(result))
  return result

def run_command(ctx):
  step_data = read_from_yaml_file(ctx['step'])
  command = step_data.get('command')
  step_options = step_data.get('options') or []
  options = get_yaml(ctx['options']) or {}
  option_params = get_option_params(step_options, options)
  params = {**option_params, **(step_data.get('params') or {})}
  logger.info('Final params: {}'.format(params))
  dependencies = set(step_data.get('dependencies') or [])
  fail_reason = verify_dependencies(ctx, step_data.get('id'), dependencies)
  if fail_reason is not None:
    return step_skipped(ctx, fail_reason)
  enable = params.get('enable')
  if enable is not None and not enable:
    logger.info('Step \'{}\' disabled. Return success'.format(ctx['step_dir']))
    return step_success(ctx)
  command_func = get_command_runner(command)
  if command_func is not None:
    return command_func(ctx, params)
  raise Exception('Invalid command \'{}\' for step \'{}\''.format(
    command,
    ctx['step']
  ))
