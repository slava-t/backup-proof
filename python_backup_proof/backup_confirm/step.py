import os
import re
import sys

from backup_confirm.logger import get_logger
from backup_confirm.utils import write_to_yaml_file, read_from_yaml_file

STEP_ID_LEN = 4
STEP_ID_RE = re.compile('^[0-9]{4}$')

logger = get_logger('step')

def get_next_id(stepname):
  id, _ = split_stepname(stepname)
  if not id is None:
    return id + 1

def step_success(ctx):
  status = {
    'status': 'success'
  }
  write_to_yaml_file(status, ctx['step_status'])

def step_failed(ctx, reason='unknown'):
  status = {
      'status': 'failed',
      'reason': reason
  }
  write_to_yaml_file(status, ctx['step_status'])

def step_skipped(ctx, reason='unknown'):
  status = {
      'status': 'skipped',
      'reason': reason
  }
  write_to_yaml_file(status, ctx['step_status'])

def verify_dependencies(ctx, step_id, dependencies = None):
  steps_dir = ctx['steps_dir']
  step_names = sorted(os.listdir(steps_dir))

  if dependencies is None:
    dependencies = set()
    for step_name in step_names:
      id, name = split_stepname(step_name)
      if id < step_id:
        dependencies.add(name)
      else:
        break

  if len(dependencies) == 0:
    return

  verified_set = set()
  unmet_list = []
  for step_name in step_names:
    _, name = split_stepname(step_name)
    if name in dependencies:
      status_path = os.path.join(steps_dir, step_name, 'status.yaml')
      status_content = read_from_yaml_file(status_path)
      if status_content.get('status') == 'success':
        verified_set.add(name)
      else:
        unmet_list.append(step_name)
  if len(unmet_list) > 0:
    return 'Unmet dependencies: {}'.format(unmet_list)
  unverified = sorted(list(dependencies.difference(verified_set)))
  if len(unverified) > 0:
    return 'Could not find dependencies: {}'.format(unverified)

def create_step(ctx, id, data):
    status = {
      'status': 'start'
    }
    step_dirname = get_step_dirname(id, data.get('name') or 'unknown')
    logger.info('Creating step \'{}\''.format(step_dirname))
    ctx = get_step_context(ctx, step_dirname)
    step_dir = ctx['step_dir']
    if os.path.isdir(step_dir):
      raise Exception('Directory \'{}\' already exists'.format(step_dir))
    os.mkdir(step_dir)
    step_data = data.copy()
    step_data['id'] = id
    write_to_yaml_file(status, ctx['step_status'])
    write_to_yaml_file(step_data, ctx['step'])
    return step_dirname

def create_steps(ctx, start_index, steps):
  index = start_index
  for step in steps:
    create_step(ctx, index, step)
    index += 1
  return index

def create_star_step(
    ctx,
    step_id,
    step_name,
    steps_path,
    steps_after = [],
    description=None
):
  logger.info('Creating star step \'{}-{}\''.format(step_id, step_name))
  if description is None:
    description = 'Create confirm steps from {}'.format(steps_path)
  step_data = {
    'name': step_name,
    'command': '*',
    'description': description,
    'params': {
      'path': steps_path,
      'steps': steps_after
    }
  }
  return create_step(ctx, step_id, step_data)

def split_stepname(stepname, throw = True):
  stepname_parts = stepname.split('-')
  if len(stepname_parts) < 2:
    if throw:
      raise Exception(
        'Step name \'{}\' does not consist of at least two parts'.format(stepname)
      )
    return (None, None)
  id = stepname_parts[0]
  if not STEP_ID_RE.match(id):
    if throw:
      raise Exception((
        'Invalid id \'{}\' in the step name \'{}\''.format(
          id,
          stepname
        )
      ))
    return (None, None)
  return (int(id), '-'.join(stepname_parts[1:]))

def get_step_dirname(step_id, name):
  return '{}-{}'.format(str(step_id).rjust(STEP_ID_LEN, '0'), name)

def save_step_status(ctx, status):
  try:
    write_to_yaml_file(status, ctx['step_status'])
  except:
    exc_type, exc_value = sys.exc_info()[:2]
    logger.error('Writing step status failed. status: {}, ctx: {}'.format(
      status,
      ctx
    ))
    logger.info('exception type: {}'.format(exc_type))
    logger.info('exception value: {}'.format(exc_value))

def get_step_context(ctx, stepname):
  step_ctx = ctx.copy()
  step_dir = os.path.join(step_ctx['steps_dir'], stepname)
  step_ctx['step_dir'] = step_dir
  step_ctx['step_status'] = os.path.join(step_dir, 'status.yaml')
  step_ctx['step'] = os.path.join(step_dir, 'step.yaml')
  return step_ctx

def generate_next_step_id(ctx):
  stepnames = sorted(os.listdir(ctx['steps_dir']))
  if len(stepnames) == 0:
    return 0
  id = get_next_id(stepnames[-1])
  if id is None:
    raise Exception('Invalid step directory name \'{}\''.format(
      stepnames[-1]
    ))
  return id

def get_next_step(ctx, stepname=None):
  stepnames = sorted(os.listdir(ctx['steps_dir']))
  indexes = [i for i, n in enumerate(stepnames) if n == stepname]
  if len(indexes) == 0:
    raise Exception('Could not find step \'{}\'.'.format(stepname))
  index = indexes[0] + 1
  if index < len(stepnames):
    return stepnames[index]
  return 'end'

