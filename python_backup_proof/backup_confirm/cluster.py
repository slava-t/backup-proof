from datetime import datetime, timezone
import yaml
import os
import shutil
import subprocess
import sys
import time
import traceback

DIR_ID_LEN = 4

from backup_confirm.context import (
  get_step_cluster_context,
  get_host_step_cluster_context,
  step_to_host_context
)
from backup_confirm.logger import get_logger
from backup_confirm.utils import write_to_yaml_file
logger = get_logger('cluster')

def format_dir_id(id):
  return str(id).rjust(DIR_ID_LEN, '0')

def get_dirname(id, dir_path):
  return '{}-{}'.format(format_dir_id(id), os.path.split(dir_path)[1])


def destroy_cluster(ctx):
  try:
    if ctx is None:
      return
    main_dir = ctx.get('main_dir')
    logger.info('Destroying cluster \'{}\''.format(main_dir))
    if os.path.isfile(ctx['docker-compose']):
      subprocess.run(
        [
          '/usr/local/bin/docker-compose',
          'down'
        ],
        cwd=main_dir,
        check=False
      )
    logger.info('Removing cluster directory \'{}\''.format(main_dir))
    #TODO for testing
    #shutil.rmtree(main_dir)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Destroying cluster \'{}\' failed: {}'.format(
      ctx.get('main_dir'),
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))

def wait_for_success(
    ctx,
    service,
    command,
    timeInSeconds=300,
    intervalInSeconds=2
):
  try:
   start = datetime.now(timezone.utc)
   logger.info('Waiting for success running command {} in \'{}\''.format(
     command,
     ctx['main_dir']
   ))
   while True:
     time.sleep(intervalInSeconds)
     result, _, stderr = exec_in_cluster(ctx, service, command)
     if result == 0:
       return True
     logger.info('Executing command {} in cluster \'{}\' failed: {}'.format(
       command,
       ctx['main_dir'],
       str(stderr).strip()
     ))
     now = datetime.now(timezone.utc)
     if (now - start).total_seconds() > timeInSeconds:
       return False
     logger.info('Waiting longer for service \'{}\' in \'{}\''.format(
       service,
       ctx['main_dir']
     ))

  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Waiting for success failed for \'{}\': {}'.format(
      ctx.get('main_dir'),
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    ))

def exec_in_cluster(ctx, service, command):
  dc_command = [
    '/usr/local/bin/docker-compose',
    'exec',
    '-T',
    service
  ]
  dc_command += command
  result = subprocess.run(
    dc_command,
    cwd=ctx['main_dir'],
    capture_output=True,
    text=True,
  )
  return (result.returncode, result.stdout, result.stderr)

def create_step_cluster(step_ctx, services):
  cluster_ctx = None
  try:
    cluster_ctx = get_step_cluster_context(step_ctx)
    host_cluster_ctx = get_host_step_cluster_context(step_ctx)
    resources_dir = cluster_ctx['resources_dir']
    host_resources_dir = host_cluster_ctx['resources_dir']

    step_host_ctx = step_to_host_context(step_ctx)
    dirs_dir = cluster_ctx.get('dirs_dir')
    logger.info('Creating all dirs for \'{}\''.format(dirs_dir))
    os.makedirs(cluster_ctx['dirs_dir'], mode=0o660, exist_ok=True)
    os.makedirs(resources_dir, mode=0o660, exist_ok=True)
    docker_compose_path = cluster_ctx.get('docker-compose')
    dc_services = {}
    for name, service in services.items():
      dc_service = {}
      dc_service['image'] = service.get('image')
      dc_service['restart'] = service.get('restart') or 'unless-stopped'
      dc_service['networks'] = ['borg']
      environment = service.get('environment')
      if environment is not None:
        dc_service['environment'] = environment
      command = service.get('command')
      if command is not None:
        dc_service['command'] = command
      dc_volumes = ['{}:/parts:ro'.format(step_host_ctx['parts_dir'])]
      dc_volumes += service.get('volumes') or []
      dirs = service.get('dirs') or []
      dir_id = 0
      for dir_path in dirs:
        dirname = get_dirname(dir_id, dir_path)
        dir_cluster_path = os.path.join(host_cluster_ctx['dirs_dir'], dirname)
        dc_volumes.append('{}:{}'.format(dir_cluster_path, dir_path))
      resources = service.get('resources') or []
      src_resources_dir = os.path.join(
        os.path.split(__file__)[0],
        'cluster-resources'
      )
      for resource in resources:
        resource_id = resource.get('id')
        dest_path = resource.get('path')
        if resource_id is None:
          raise Exception('Missing resource_id: {}'.format(resource))
        if dest_path is None:
          raise Exception('Missing path in resource: {}'.format(resource))
        src_resource_dir = os.path.join(src_resources_dir, resource_id)
        if not os.path.isdir(src_resource_dir):
          raise Exception('Could not find resource \'{}\''.format(
            src_resource_dir
          ))
        dest_resource_dir = os.path.join(
          resources_dir,
          resource_id
        )
        host_dest_resource_dir = os.path.join(
          host_resources_dir,
          resource_id
        )
        shutil.copytree(src_resource_dir, dest_resource_dir)
        dc_volumes.append('{}:{}:ro'.format(host_dest_resource_dir, dest_path))
      dc_service['volumes'] = dc_volumes
      dc_services[name] = dc_service
    dc_content = {
      'version': '3.5',
      'services': dc_services,
      'networks': {
        'borg': {
          'name': 'borgnet',
          'external': True
        }
      }
    }
    logger.info('Writting docker-compose content to \'{}\': \n{}\n'.format(
      docker_compose_path,
      yaml.dump(dc_content, default_flow_style=False)
    ))
    write_to_yaml_file(dc_content, docker_compose_path)
    subprocess.run(
      [
        '/usr/local/bin/docker-compose',
        'up',
        '-d'
      ],
      cwd=cluster_ctx['main_dir'],
      check=True
    )
    cluster_ctx['success'] = True
    return cluster_ctx
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Creating step cluster error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))
  return cluster_ctx

