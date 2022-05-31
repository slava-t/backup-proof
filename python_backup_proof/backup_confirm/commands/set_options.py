import yaml
from backup_confirm.logger import get_logger
from backup_confirm.step import step_success
from backup_confirm.utils import get_yaml, write_to_yaml_file

logger = get_logger('set_options')
def run_set_options(ctx, params):
  options_path = ctx['options']
  options = get_yaml(ctx['options']) or {}
  logger.info('Old options: \n{}\n'.format(
    yaml.dump(options, default_flow_style=False)
  ))
  new_options = {**options, **params}
  logger.info('New options: \n{}\n'.format(
    yaml.dump(new_options, default_flow_style=False)
  ))
  write_to_yaml_file(new_options, options_path)
  step_success(ctx)

