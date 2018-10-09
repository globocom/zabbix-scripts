#!/usr/bin/python
"""
Copyright (c) 2018.
This file is part of globocom/zabbix-scripts
(see https://github.com/globocom/zabbix-scripts).
License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
"""
from __future__ import division
from os import path
from sys import argv, exit
from progressbar import ProgressBar, Percentage, ETA, ReverseBar, RotatingMarker, Timer
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from math import ceil
from logprint import LogPrint

parser = ArgumentParser(description = 'Changes all passive proxies to active')

parser.add_argument('--url', dest = 'url', help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Don\'t show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')

parser.add_argument('--hosts', dest = 'hosts', action = 'store_true', help = 'Disable all hosts inside zabbix')
parser.add_argument('--no-hosts', dest = 'hosts', action = 'store_false', help = 'Keep the state as is, from all hosts')
parser.set_defaults(host=True)
parser.add_argument('--proxy', dest = 'proxy', action = 'store_true', help = 'Change all proxies to active')
parser.add_argument('--no-proxy', dest = 'proxy', action = 'store_false', help = 'Dont change proxy mode')
parser.set_defaults(proxy=False)
parser.add_argument('--proxy-local', dest = 'proxy_local', action = 'store_true', help = 'Change all passive proxies to localhost')
parser.add_argument('--no-proxy-local', dest = 'proxy_local', action = 'store_false', help = 'Dont change passive proxies address')
parser.set_defaults(proxy_local=False)
parser.add_argument('--discovery', dest = 'discovery', action = 'store_true', help = 'Disable all network discovery rules')
parser.add_argument('--no-discovery', dest = 'discovery', action = 'store_false', help = 'Keep state of all network discovery rules')
parser.set_defaults(discovery=True)
parser.add_argument('--mail', dest = 'mail', action = 'store_true', help = 'Change email source address to zabbix-AMBIENTE@suaempresa.com')
parser.add_argument('--no-mail', dest = 'mail', action = 'store_false', help = 'Keep current email source address')
parser.set_defaults(mail=True)
args = parser.parse_args()

TIMEOUT = 180.0
LOGFILE = '/tmp/%s.log' % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())

try:
  zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
  zapi.login(args.user,args.password)
except Exception, e:
    logger.error('Unable to login: %s' % (e))
    exit(1)

# Grupos a manter ativo apos desabilitar todos. Usar IDs.
groupids = [ 4 ] # Zabbix Servers

def hosts_disable_all():
  """
  status de host 0 = enabled
  status de host 1 = disabled
  """
  logger.info('Disabling all hosts, in blocks of 1000')
  hosts = zapi.host.get(output=[ 'hostid' ], search={ 'status': 0 })
  maxval = int(ceil(hosts.__len__())/1000+1)
  bar = ProgressBar(maxval=maxval,widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
  i = 0
  for i in xrange(maxval):
    block = hosts[:1000]
    del hosts[:1000]
    result = zapi.host.massupdate(hosts=[ x for x in block ], status=1)
    i += 1
    bar.update(i)
  bar.finish()
  logger.info('Done')
  return

def hosts_enable_selected():
  """
  TODO:
  Ativar apenas os hosts dos grupos desejados
  """
  logger.info('Enabling selected hosts')
  hosts = zapi.host.get(output=[ 'hostid' ], groupids=groupids, search={ 'status': 1 })
  result = zapi.host.massupdate(hosts=[ x for x in hosts ], status=0)
  logger.info('Done')
  return

def proxy_passive_to_active():
  """
  status de prxy 5 = active
  status de prxy 6 = passive
  """
  logger.info('Change all proxys to active')
  proxys = zapi.proxy.get(output=[ 'shorten', 'host' ],
    filter={ 'status': 6 })
  if ( proxys.__len__() == 0 ):
    logger.info('Done')
    return
  bar = ProgressBar(maxval=proxys.__len__(),widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
  i = 0
  for x in proxys:
    i += 1
    proxyid = x['proxyid']
    result = zapi.proxy.update(proxyid=proxyid, status=5)
    logger.echo = False
    logger.debug('Changed from passive to active proxy: %s' % (x['host']))
    bar.update(i)
  bar.finish()
  logger.echo = True
  logger.info('Done')
  return

def proxy_passive_to_localhost():
  logger.info('Change all passive proxys to localhost')
  proxys = zapi.proxy.get(output=[ 'extend', 'host' ],filter={'status': 6}, selectInterface='extend')
  if ( proxys.__len__() == 0 ):
    logger.info('Done')
    return
  bar = ProgressBar(maxval=proxys.__len__(),widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
  i = 0
  for x in proxys:
    proxyid = x['proxyid']
    params = {
      'proxyid': proxyid,
      'status': 6,
      'interface': {
        'interfaceid': x['interface']['interfaceid'],
        'dns': 'localhost',
        'ip': '127.0.0.1'
      }
    }
    result = zapi.proxy.update(**params)
    logger.debug('Proxy changed to localhost: %s' % (x['host']))
    i += 1
    logger.echo = False
    bar.update(i)
  logger.echo = True
  bar.finish()
  logger.info('Done')
  return

def discovery_disable_all(status=0):
  """
  Alterar status de todos os discoveries *auto*
  Status 0 = enable
  Status 1 = disable
  """ 
  logger.info('Disabling all network discoveries')
  druleids = zapi.drule.get(output=[ 'druleid', 'iprange', 'name', 'proxy_hostid', 'status' ],
      selectDChecks='extend', filter={ 'status': 0 })
  if ( druleids.__len__() == 0 ):
    logger.info('Done')
    return
  bar = ProgressBar(maxval=druleids.__len__(),widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
  i = 0
  for x in druleids:
    params_disable = {
      'druleid': x['druleid'],
      'iprange': x['iprange'],
      'name': x['name'],
      'dchecks': x['dchecks'],
      'status': 1
    }
    out = zapi.drule.update(**params_disable)
    logger.echo = False
    if out:
      logger.debug('\tNew status: %s (%s) --> %d' % (x['name'],out['druleids'],status))
    else:
      logger.warning('\tFAILED to change status: %s (%s) --> %d' % (x['name'],out['druleids'],status))
    i += 1
    bar.update(i)
  logger.echo = True
  bar.finish()
  logger.info('Done')
  return

def mail_src():
  """
  Ajusta a fonte de emails do zabbix.
  Depende da url de consulta.
  """
  email = 'zabbix@zabbix.%s' % args.url.split('zabbix.')[1]
  logger.info('Updating source of email address to %s' % email)
  out = zapi.mediatype.update(mediatypeid=1,smtp_email=email)
  logger.info('Done')


if ( args.proxy ):
  proxy_passive_to_active()

if ( args.hosts ):
  hosts_disable_all()
  hosts_enable_selected()

if ( args.discovery ):
  discovery_disable_all()

if ( args.proxy_local ):
  proxy_passive_to_localhost()

if ( args.mail ):
  mail_src()
zapi.user.logout()
