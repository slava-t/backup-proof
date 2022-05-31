from os import listdir
from os.path import join, isdir, exists
import yaml

from backup_confirm.logger import get_logger
from backup_confirm.utils import read_from_yaml_file

CONFIG_PATH = '/backup/config/.config.yaml'
ENC_CONFIG_PATH = '/backup/enc/.config.yaml'

config = None
enc_config = None

logger = get_logger('config')

def get_config():
    global config
    if config is None:
      config = read_from_yaml_file(CONFIG_PATH)
    return config

def get_enc_config():
  global enc_config
  if enc_config is None:
    enc_config = read_from_yaml_file(ENC_CONFIG_PATH)
  return enc_config



