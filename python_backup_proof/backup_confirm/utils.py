from datetime import datetime, timezone
import yaml

def extract_datetime(archive_id):
  year = int(archive_id[0:4])
  month = int(archive_id[4:6])
  day = int(archive_id[6:8])
  hour = int(archive_id[8:10])
  minute = int(archive_id[10:12])
  second = int(archive_id[12:14])
  ms = int(archive_id[14:20])
  return datetime(year, month, day, hour, minute, second, ms, timezone.utc)

def write_to_yaml_file(data, yaml_path):
  with open(yaml_path, 'w') as stream:
    yaml.dump(data, stream)

def read_from_yaml_file(yaml_path):
  with open(yaml_path, 'r') as stream:
    return yaml.safe_load(stream)
