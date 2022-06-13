import json
import sys
import traceback

from backup_confirm.config import get_enc_config
from backup_confirm.logger import get_logger
import backup_confirm.wrapped_requests as requests
from backup_confirm.report import get_backup_outcome, create_text_report

logger = get_logger('notification')

def notify(report_data):
  try:
    outcome = get_backup_outcome(report_data)
    logger.info('Backup outcome:\n {}'.format(json.dumps(outcome, indent = 2)))
    config = get_enc_config()
    base_url = config.get('notification_url')
    if base_url is None:
      logger.error('Missing \'notification_url\' in configuration')
      return
    uri = 'backup-{}-{}-{}'.format(
      outcome['zone'],
      outcome['product'],
      outcome['environment']
    )
    url = '{}/{}'.format(base_url, uri)
    lines = create_text_report(outcome)
    text = '\n'.join(lines)
    backup_success = outcome.get('backup', False)
    title = 'Backup {}notification'.format(
      '' if backup_success else 'failure '
    )
    logger.info('Report title for: \'{}\''.format(title))
    logger.info('Report content for \'{}\':\n{}'.format(uri, text))
    data = {
      'success': outcome.get('backup', False),
      'title': title,
      'text': text
    }
    requests.post(url, json=data)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logger.error('Notification error: {}'.format(''.join(
      traceback.format_exception(exc_type, exc_value, exc_traceback)
    )))


