import os

from backup_confirm.logger import get_logger
from backup_confirm.utils import read_from_yaml_file

from backup_confirm.step import (
  create_star_step,
  create_steps,
  step_success,
  generate_next_step_id
)

logger = get_logger('star command')

def split_steps(steps, steps_after):
  all_steps = steps + steps_after
  star_index = next(
    (i for i, x in enumerate(all_steps) if x.get('command') == '*'),
    None
  )
  if star_index is None:
    return (all_steps, None, [])
  return (
    all_steps[:star_index],
    all_steps[star_index],
    all_steps[star_index+1:]
  )


def run_star_command(ctx, params):
  logger.info('----------------run_star_command: {}'.format(params))
  steps_after = params.get('steps') or []
  next_id = generate_next_step_id(ctx)
  steps_path = params.get('path')
  if type(steps_after) is not list:
    raise Exception('\'*\' command expects steps in params to be a list')
  steps_content = read_from_yaml_file(steps_path)
  steps = steps_content.get('steps')
  if type(steps) is not list:
    raise Exception(
      '\'*\' command expects steps to be present and to be a list'
    )
  before, star, after = split_steps(steps, steps_after)
  logger.info('>>>>>>>>>before: {}'.format(before))
  logger.info('>>>>>>>>>star: {}'.format(star))
  logger.info('>>>>>>>>>after: {}'.format(after))
  next_id = create_steps(ctx, next_id, before)
  if star is not None:
    params = star.get('params') or {}
    steps_path = params.get('path')
    if steps_path is None:
      raise Exception('Missing \'path\' parameter in \'*\' command')
    create_star_step(
      ctx,
      next_id,
      star.get('name') or 'star',
      steps_path,
      steps_after=after,
      description=star.get('desctiption')
    )
#    create_steps(ctx, next_id + 1, after)
  step_success(ctx)

