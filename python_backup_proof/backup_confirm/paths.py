import os
CONFIG_PATH = '/backup/.config/.config.yaml'
ENC_CONFIG_PATH = '/backup/enc/.config.yaml'
ENC_PROCESS_DIR = '/backup/enc/process'
VERIFIED_DIR = '/backup/enc/verified'
CLUSTER_DIR = '/backup/enc/cluster'
FAILED_DIR = '/backup/enc/failed'
RELEASE_DIR = '/backup/var/ready'
PUBLISH_DIR = '/backup/var/public'
LOG_DIR = '/backup/var/logs'
CONFIRM_LOG_PATH = os.path.join(LOG_DIR, 'backup-confirm.log')
COMPLETE_LOG_PATH = os.path.join(LOG_DIR, 'backup-complete.log')
ZPOOL_STATUS_PATH = '/backup/var/zpool_status'

HOST_ENC_PROCESS_DIR = '/data/confirm/enc/process'
HOST_CLUSTER_DIR = '/data/confirm/enc/cluster'

