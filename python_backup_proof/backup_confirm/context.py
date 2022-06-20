import os

from backup_confirm.paths import (
  CLUSTER_DIR,
  HOST_CLUSTER_DIR,
  ENC_PROCESS_DIR,
  HOST_ENC_PROCESS_DIR
)
from backup_confirm.utils import (
  format_step_id,
  parse_process_name,
  split_stepname
)

def get_host_process_context(process_name):
  return get_process_context(
    os.path.join(HOST_ENC_PROCESS_DIR, process_name)
  )

def get_process_context(root_dir):
  return {
    'main_dir': root_dir,
    'parts_dir': os.path.join(root_dir, 'parts'),
    'steps_dir': os.path.join(root_dir, 'steps'),
    'parts': os.path.join(root_dir, 'parts.yaml'),
    'steps': os.path.join(root_dir, 'steps.yaml'),
    'status': os.path.join(root_dir, 'status.yaml'),
    'docker-compose': os.path.join(root_dir, 'docker-compose.yaml')
  }

def get_step_context(ctx, stepname):
  step_ctx = ctx.copy()
  step_dir = os.path.join(step_ctx['steps_dir'], stepname)
  step_ctx['step_dir'] = step_dir
  step_ctx['step_status'] = os.path.join(step_dir, 'status.yaml')
  step_ctx['step'] = os.path.join(step_dir, 'step.yaml')
  return step_ctx

def get_process_descriptor(ctx):
  return parse_process_name(os.path.split(ctx['main_dir'])[1])

def get_host_step_cluster_context(ctx):
  return get_step_cluster_context(ctx, root_dir = HOST_CLUSTER_DIR)

def step_to_host_context(step_ctx):
  pd = get_process_descriptor(step_ctx)
  host_process_ctx = get_host_process_context(pd['orig'])
  stepname = os.path.split(step_ctx['step_dir'])[1]
  return get_step_context(host_process_ctx, stepname)

def get_step_cluster_context(ctx, root_dir = CLUSTER_DIR):
  process_descriptor = get_process_descriptor(ctx)
  stepname = os.path.split(ctx['step_dir'])[1]
  step_id, _ = split_stepname(stepname)
  name = '{}-{}'.format(process_descriptor['orig'], format_step_id(
    step_id
  ))
  main_dir = os.path.join(root_dir, name)

  dc_path = os.path.join(main_dir, 'docker-compose.yaml')
  return {
    'name': name,
    'main_dir': main_dir,
    'dirs_dir': os.path.join(main_dir, 'dirs'),
    'step_id': step_id,
    'process': process_descriptor,
    'docker-compose': dc_path
  }
