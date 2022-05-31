from backup_confirm.vars import BACKUP_PROOF_IMAGE

def get_proof_service_dict(command, environment, volumes):
  result = {
    'image': BACKUP_PROOF_IMAGE,
    'restart': 'no',
    'networks': ['common']
  }

  if command is not None:
    result['command'] = command

  if volumes is not None:
    result['volumes'] = volumes

  if environment is not None:
    result['environment'] = environment

  return result



