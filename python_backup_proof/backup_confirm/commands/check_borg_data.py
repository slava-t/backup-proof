from backup_confirm.borg import check_borg_data
from backup_confirm.step import step_success, step_failed

def run_check_borg_data(ctx, _):
  if check_borg_data():
    return step_success(ctx)
  step_failed(ctx, 'Checking borg data failed')

