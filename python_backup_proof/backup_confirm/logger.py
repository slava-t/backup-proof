import logging

import logging.config
LOG_LEVEL=logging.INFO
#TODO take the filename for the logger from an environment variable
logging.basicConfig(
  filename='/var/log/backup_confirm.log',
  format='%(asctime)-15s [%(name)s] [%(levelname)s] - %(message)s',
  level = LOG_LEVEL
)

def get_logger(name='confirm'):
  return logging.getLogger(name)

