import os

from backup_confirm.logger import get_logger
from backup_confirm.step import step_success
from backup_confirm.utils import read_from_yaml_file, write_to_yaml_file
from backup_confirm.confirm_vars import CONFIRM_ZONE, CONFIRM_ENVIRONMENT

logger = get_logger('create_confirm_steps_yaml')
def run_create_confirm_steps_yaml(ctx, _):
  spec_path = os.path.join(ctx['parts_dir'], 'confirm/confirm/spec.yaml')
  spec = read_from_yaml_file(spec_path)
  spec_steps = spec.get('steps')
  if type(spec_steps) is not list:
    raise Exception(
      'Expected \'steps\' to be present in spec.yaml and to be an array'
    )
  confirm_steps = []
  for spec_step in spec_steps:
    zones = spec_step.get('zones')
    envs = spec_step.get('environments')
    zone_ok = zones is None or CONFIRM_ZONE in zones
    env_ok = envs is None or CONFIRM_ENVIRONMENT in envs
    if zone_ok and env_ok:
      confirm_steps.append(spec_step)
    else:
      logger.info('Skipping confirm step \'{}\''.format(
        spec_step.get('name') or 'unknown'
      ))
  yaml_content = {
    'steps': confirm_steps
  }
  write_to_yaml_file(
    yaml_content,
    os.path.join(ctx['main_dir'], 'confirm_steps.yaml')
  )
  step_success(ctx)
