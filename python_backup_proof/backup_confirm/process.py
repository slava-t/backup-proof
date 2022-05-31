import os
import secrets
import subprocess
import sys
import time

from backup_confirm.logger import get_logger
from backup_confirm.utils import write_to_yaml_file, read_from_yaml_file
from backup_confirm.vars import BACKUP_PROOF_IMAGE

CONFIRM_PROCESS_PATH_VAR = 'CONFIRM_PROCESS_PATH'
CONFIRM_PROCESS_PATH = os.environ.get(CONFIRM_PROCESS_PATH_VAR)
ENC_PROCESS_DIR = '/backup/enc/process'
logger = get_logger('process')


def get_process_context(root_dir):
  return {
    'parts_dir': os.path.join(root_dir, 'parts'),
    'steps_dir': os.path.join(root_dir, 'steps'),
    'parts': os.path.join(root_dir, 'parts.yaml'),
    'steps': os.path.join(root_dir, 'steps.yaml'),
    'status': os.path.join(root_dir, 'status.yaml'),
    'docker-compose': os.path.join(root_dir, 'docker-compose.yaml')
  }

def create_process(prod_env_id, parts):
  confirm_part = parts.get('confirm')
  id = confirm_part.get('id')
  process_id = '{}-{}'.format(prod_env_id, id)
  process_tmp_id = '{}-{}'.format(process_id, secrets.token_hex(8))
  process_path = os.path.join(ENC_PROCESS_DIR, process_id)
  process_tmp_path = os.path.join(ENC_PROCESS_DIR, process_tmp_id)
  tmp_ctx = get_process_context(process_tmp_path)


  if not os.path.isdir(process_path):
    os.mkdir(process_tmp_path, 0o600)
    os.mkdir(tmp_ctx['parts_dir'], 0x600)
    os.mkdir(tmp_ctx['steps_dir'], 0o600)
    parts_content = {
      'product': prod_env_id,
      'parts': parts
    }
    write_to_yaml_file(
      parts_content,
      tmp_ctx['parts']
    )
    steps_content = {
      'steps': [{
        'name': 'extract_confirm',
        'command': 'extract_part confirm'
      }, {
        'name': 'extract_logs',
        'command': 'extract_part logs'
#      }, {
#        'name': 'verify_sha1sum_confirm',
#        'command': 'verify_sha1sum confirm',
#        'dependencies': ['extract_confirm']
#      }, {
#        'name': 'verify_sha1sum_logs',
#        'command': 'verify_sha1sum logs',
#        'dependencies': ['extract_logs']
#      }, {
#        'name': 'create_confirm_steps',
#        'command': 'create_confirm_steps',
#        'dependencies': ['verify_sha1sum_confirm']
#      }, {
#        'name': 'run_confirm_steps',
#        'command': 'run_steps confirm_steps.yaml',
#        'dependencies': ['create_confirm_steps']
#      }, {
#        'name': 'close',
#        'command': 'close_process'
      }]
    }
    write_to_yaml_file(
      steps_content,
      tmp_ctx['steps']
    )

    status_content = {
      'status': 'start'
    }
    write_to_yaml_file(
      status_content,
      tmp_ctx['status']
    )

    compose_content = {
      'version': '3.5',
      'services': {
        'confirm': {
          'volumes':[
            '/data/enc:/enc',
            '/data/backup/.config:/backup/config',
            '/data/backup/state:/backup/state',
            '/data/backup/enc:/backup/enc'
          ],
          'image': BACKUP_PROOF_IMAGE,
          'restart': 'unless-stopped',
          'environment': {
            'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'yes',
            CONFIRM_PROCESS_PATH_VAR: process_path
          },
          'command': '/usr/local/bin/run_confirm_process'
        }
      }
    }
    write_to_yaml_file(
      compose_content,
      tmp_ctx['docker-compose']
    )
    os.rename(process_tmp_path, process_path)
    subprocess.run(
      [
        'docker-compose',
        'up',
        '-d'
      ],
      cwd=process_path,
      check=True
    )

def create_processes(parts):
  for prod_env_id, parts in parts.items():
    create_process(prod_env_id, parts)


def process():
  if not CONFIRM_PROCESS_PATH:
    return
  ctx = get_process_context(CONFIRM_PROCESS_PATH)
  status_content = read_from_yaml_file(ctx['status']) or {}
  status = status_content['status']
  if not status_content['status']:
    logger.error('No \'status\' in status.yaml')
    return
  if status == 'end':
    return
  if status != 'step':
    logger.error('Unexpected status \'{}\''.format(status))
    return

  step = status_conten['step']
  
def main():
    count = 0
    while True:
      try:
        process()
        count += 1
        subprocess.run(
          [
            'bash',
            '-c',
            'echo "{}" >>/var/log/process_count.log'.format(count)
          ],
          check=True
        )
        time.sleep(5)
      except:
        logger.error('Processing error')
        exc_type, exc_value = sys.exc_info()[:2]
        logger.info('exception type: {}'.format(exc_type))
        logger.info('exception value: {}'.format(exc_value))
