from backup_confirm.step import step_success, step_failed, verify_dependencies
from backup_confirm.utils import read_from_yaml_file

def run_verify_preceeding_steps(ctx):
  step_data = read_from_yaml_file(ctx['step'])
  fail_reason = verify_dependencies(ctx, step_data['id'])
  if fail_reason is not None:
    return step_failed(ctx, fail_reason)
  step_success(ctx)
