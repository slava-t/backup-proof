import logging

import logging.config

from backup_confirm.confirm_vars import CONFIRM_PROCESS_LOG
LOG_LEVEL=logging.INFO
#TODO take the filename for the logger from an environment variable

log_path = '/backup/logs/backup-confirm.log'

if CONFIRM_PROCESS_LOG:
  log_path = CONFIRM_PROCESS_LOG

logging.basicConfig(
  filename=log_path,
  format='%(asctime)-15s [%(name)s] [%(levelname)s] - %(message)s',
  level = LOG_LEVEL
)

def get_logger(name='confirm'):
  return logging.getLogger(name)

