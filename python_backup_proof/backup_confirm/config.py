from backup_confirm.logger import get_logger
from backup_confirm.paths import ENC_CONFIG_PATH, CONFIG_PATH
from backup_confirm.utils import get_yaml

enc_config = None
config = None

logger = get_logger('config')

def get_enc_config():
  global enc_config
  if enc_config is None:
    enc_config = get_yaml(ENC_CONFIG_PATH)
  return enc_config

def get_config():
  global config
  if config is None:
    config = get_yaml(CONFIG_PATH)
  return config



