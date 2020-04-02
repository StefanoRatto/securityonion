#!py

import logging
import sys

allowed_functions = ['is_enabled,zeek']
states_to_apply = []


def apply_states(states=''):

  calling_func = sys._getframe().f_back.f_code.co_name
  logging.debug('healthcheck_module: apply_states function caller: %s' % calling_func)

  if not states:
    states = ','.join(states_to_apply)
 
  if states: 
    logging.info('healthcheck_module: apply_states states: %s' % str(states))
    __salt__['state.apply'](states)


def docker_stop(container):
  
  try:
    stopdocker = __salt__['docker.rm'](container, 'stop=True')
  except Exception as e:
    logging.error('healthcheck_module: %s' % e)


def is_enabled():
  
  if __salt__['pillar.get']('healthcheck:enabled', 'False'):
    retval = True
  else:
    retval = False
  
  return retval
  

def run(checks=''):
  
  retval = []
  calling_func = sys._getframe().f_back.f_code.co_name
  logging.debug('healthcheck_module: run function caller: %s' % calling_func)
  
  if checks:
    checks = checks.split(',')
  else:  
    checks = __salt__['pillar.get']('healthcheck:checks', {})
  
  logging.debug('healthcheck_module: run checks to be run: %s' % str(checks))
  for check in checks:
    if check in allowed_functions:
      retval.append(check)
      check = getattr(sys.modules[__name__], check)
      check()
    else:
      logging.warning('healthcheck_module: attempted to run function %s' % check)

  # If you want to apply states at the end of the run,
  # be sure to append the state name to states_to_apply[]
  apply_states()

  return retval


def zeek():

  calling_func = sys._getframe().f_back.f_code.co_name
  logging.info('healthcheck_module: zeek function caller: %s' % calling_func)
  retval = []

  retcode = __salt__['zeekctl.status'](verbose=False)
  logging.info('healthcheck_module: zeekctl.status retcode: %i' % retcode)
  if retcode:
    zeek_restart = True
    if calling_func != 'beacon':
      docker_stop('so-zeek')
      states_to_apply.append('zeek')
  else:
    zeek_restart = False

  if calling_func == 'execute' and zeek_restart:
    apply_states()
  
  retval.append({'zeek_restart': zeek_restart})

  __salt__['telegraf.send']('healthcheck zeek_restart=%s' % str(zeek_restart))
  return retval