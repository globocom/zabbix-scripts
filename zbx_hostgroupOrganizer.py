#!/usr/bin/python
# Copyright (c) 2016, Globo.com <https://github.com/globocom>
# This file is part of globocom/zabbix-scripts
# (see https://github.com/globocom/zabbix-scripts).
# License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
from types import UnicodeType
from os import path
from sys import argv, exit
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from logprint import LogPrint

parser = ArgumentParser(description = 'Creates a hostgroup for each proxy, and adds all hosts monitored by it. Also, interacts with all hosts in Operacao organizing it.')
parser.add_argument('--url', dest = 'url', help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Dont show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
args = parser.parse_args()

TIMEOUT = 5.0
LOGFILE = '/tmp/%s.log' % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())
HGS = [ 'Operacao', 'Operacao::Servico' ]

try:
    zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
    zapi.login(args.user,args.password)
except Exception, e:
    logger.error('Unable to login: {0}'.format(e))
    exit(1)

def hg_cache():
    return zapi.hostgroup.get(output=['name'])

def hg_search(name):
    for hgx in hg_names:
        if ( hgx['name'] == name ):
            return hgx['groupid']
    return False

def hg_find(name):
    ret = []
    for hgx in hg_names:
        if ( name in hgx['name'] ):
            ret.append(hgx['groupid'])
    if (len(ret) > 0): 
        return(ret)
    else:
        return(False)

def api_validate(json_in):
    if ( type(json_in.get('message')) is UnicodeType ):
        if ( json_in['message'] == 'Invalid params.' ):
            logger.error('Invalid params. Check query below.')
            logger.print_json(json_in)
            return False
    return True

def hg_massupdate(hostsJson,hostgroupName=False,hostgroupId=False):
    if hostgroupId:
        hostgroupid = hostgroupId
        hostgroupMessage = 'id {0}'.format(hostgroupId)
    else:
        hostgroupid = hg_search(hostgroupName)
        hostgroupMessage = hostgroupName
    query = { 'groups': [ { 'groupid': hostgroupid } ], 'hosts': hostsJson }
    logger.debug(query)
    try:
        out = zapi.hostgroup.massupdate(**query)
        if ( api_validate(out) ):
            logger.info('Updated hostgroups: {0}'.format(hostgroupMessage))
        else:
            logger.warning('Error when updating hosts: {0}'.format(out['message']))
    except Exception, e:
        logger.warning('API Exception when updating hosts: {0}'.format(e))

def hg_cleangroup(hostgroupId=None):
    hostids = zapi.host.get(groupids=hostgroupId,output=['hostid'])
    zapi.hostgroup.massremove(groupids=hostgroupId,hostids=[ x['hostid'] for x in hostids ])
    return

def operacao():
    # sanity check (avoid zabbix api errors when overwriting Operacao hostgroup)
    hg_operacao = hg_search('Operacao')
    if not hg_operacao:
        logger.error('Hostgroup not found')
        return
    hosts_operacao = zapi.host.get(output=['hostid'],selectGroups=['groupid','name'],groupids=[ hg_operacao ])
    for host in hosts_operacao:
        if host['groups'].__len__() == 1:
            logger.warning('Hostid {0} is only at hostgroup {1}({2})'.format(host['hostid'],host['groups'][0]['name'],host['groups'][0]['groupid']))

    for HG in HGS:
        logger.info('Starting \'{0}\'...'.format(HG))
        hgs_operacao = hg_find('{0}::'.format(HG))
        hosts_operacao = zapi.host.get(output=['hostid'],groupids=[ x for x in hgs_operacao ])
        hg_massupdate(hostsJson=hosts_operacao,hostgroupName=HG)
    return

def proxy():
    proxies = zapi.proxy.get(output=['host'],sortfield=['host'])
    for p in proxies:
        hg_name = 'Zabbix::Proxy::{0}'.format(p['host'])
        logger.info('Starting \'{0}\''.format(hg_name))
        hg_proxy = hg_search(hg_name)
        if not hg_proxy:
            logger.debug('Creating hostgroup: {0}'.format(hg_name))
            out = zapi.hostgroup.create(name=hg_name)
            logger.print_json(out)
            hg_proxy = out['groupids'][0]
        hosts_proxy = zapi.host.get(output=['hostid'],proxyids=[p['proxyid']])
        hg_cleangroup(hostgroupId=hg_proxy)
        hg_massupdate(hostsJson=hosts_proxy,hostgroupId=hg_proxy)
    return

try:
    hg_names = hg_cache()
    operacao()
    pass
except Exception, e:
    logger.error('Failed to organize operacao hostgroups: {0}'.format(e))

try:
    hg_names = hg_cache()
    proxy()
except Exception, e:
    logger.error('Failed to organize proxy hostgroups: {0}'.format(e))

logger.info('Fim')
zapi.user.logout()
