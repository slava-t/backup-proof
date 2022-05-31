import sys

import requests # pylint: disable=no-import-requests

current_module = sys.modules[__name__]

TIMEOUT_KEY = 'timeout'
# default timeout 30 seconds
DEFAULT_TIMEOUT = 60

wrapped_functions = ['head', 'get', 'post', 'put', 'patch', 'delete']

setattr(current_module, 'exceptions', requests.exceptions)

def wrap_function(name):
  orig_function = getattr(requests, name)
  def func(*args, **kwargs):
    timeout = kwargs.get(TIMEOUT_KEY, DEFAULT_TIMEOUT)
    kwargs[TIMEOUT_KEY] = timeout
    return orig_function(*args, **kwargs)
  setattr(current_module, name, func)

for fn_name in wrapped_functions:
  wrap_function(fn_name)
