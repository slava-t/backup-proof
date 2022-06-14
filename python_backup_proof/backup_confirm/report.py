import os
import sys
import traceback

from backup_confirm.logger import get_logger
from backup_confirm.process import ENC_PROCESS_DIR
from backup_confirm.step import split_stepname
from backup_confirm.utils import get_yaml

logger = get_logger('report')


def create_process_report(process_descriptor):
  steps = []
  complete_steps = []
  report_data = {
    'report': False,
    'steps': steps,
    'complete_steps': complete_steps
  }
  try:
    process_name = process_descriptor['orig']
    logger.info('Create process report for \'{}\''.format(process_name))
    process_path = os.path.join(ENC_PROCESS_DIR, process_name)
    data_status_path = os.path.join(process_path, 'data_status.yaml')
    parts_yaml_path = os.path.join(process_path, 'parts.yaml')
    steps_dir = os.path.join(process_path, 'steps')
    data_status = get_yaml(data_status_path, {})
    logger.info('Data status for \'{}\': {}'.format(process_name, data_status))
    report_data['valid_data'] = data_status.get('status') == 'success'
    parts = get_yaml(parts_yaml_path, {})
    report_data['zone'] = parts.get('zone', 'unknown')
    report_data['product'] = process_descriptor['prod']
    report_data['environment'] = process_descriptor['env']
    report_data['fid'] = process_descriptor['fid']
    step_names = sorted(os.listdir(steps_dir))
    for step_name in step_names:
      _, name = split_stepname(step_name)
      step_dir = os.path.join(steps_dir, step_name)
      step_status_path = os.path.join(step_dir, 'status.yaml')
      step_path = os.path.join(step_dir, 'step.yaml')
      step_status = get_yaml(step_status_path, {})
      step = get_yaml(step_path)
      steps.append({
        'name': name,
        'description': step.get('description', name),
        'status': step_status.get('status', 'unknown')
      })
    report_data['report'] = True
    logger.info('Done creating process report for \'{}\''.format(
      process_name
    ))
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Processing error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))
    add_complete_step(report_data, 'report_creation', 'Creating report', False)

  return report_data

def add_complete_step(report_data, name, description, success):
  report_data['complete_steps'].append({
    'step': name,
    'description': description,
    'status': 'success' if success else 'failed'
  })

def format_report_line(status, description):
  return '  {:<10} {}'.format(status.upper(), description)

def format_bool_line(status, description):
  return format_report_line(
    'success' if status else 'failed',
    description
  )

def get_all_failed_steps(steps):
  return [x for x in steps if x.get('status', 'failed') != 'success']

def get_backup_outcome(report_data):
  failed_confirm_steps = get_all_failed_steps(report_data['steps'])
  failed_complete_steps = get_all_failed_steps(
      report_data['complete_steps']
  )
  report = report_data.get('report', False)
  valid_data = report_data.get('valid_data', False)
  confirmation = len(failed_confirm_steps) == 0
  completion = len(failed_complete_steps) == 0
  backup = report and valid_data and confirmation and completion

  return {
    'fid': report_data.get('fid', 'unknown'),
    'product': report_data.get('product', 'unknown'),
    'environment': report_data.get('environment', 'unknown'),
    'zone': report_data.get('zone', 'unknown'),
    'report': report,
    'failed_confirm_steps': failed_confirm_steps,
    'failed_complete_steps': failed_complete_steps,
    'valid_data': valid_data,
    'confirmation': confirmation,
    'completion': completion,
    'backup': backup,
    'report_data': report_data
  }

def add_steps(lines, title, steps):
  if len(steps) > 0:
    lines.append('')
    lines.append('{}:'.format(title))
    for step in steps:
      lines.append(format_report_line(
        step.get('status', 'failed'),
        step.get('description', step.get('name', 'unknown'))
      ))

def create_text_report(outcome):
  lines = []
  lines.append(
    '         Backup report {} for \'{}-{}\' in zone \'{}\''.format(
      outcome['fid'],
      outcome['product'],
      outcome['environment'],
      outcome['zone']
    )
  )
  lines.append('')
  lines.append('Backup outcome:')
  lines.append(format_bool_line(
    outcome['confirmation'],
    'All confirmation steps'
  ))
  lines.append(format_bool_line(
    outcome['valid_data'],
    'Data verification'
  ))
  lines.append(format_bool_line(
    outcome['completion'],
    'Completion steps'
  ))
  lines.append(format_bool_line(
    outcome['report'],
    'Report creation'
  ))
  lines.append(format_bool_line(
    outcome['backup'],
    'All backup steps'
  ))
  add_steps(lines, 'Failed confirmation steps', outcome['failed_confirm_steps'])
  add_steps(lines, 'Failed completion steps', outcome['failed_complete_steps'])

  return lines

