#!/usr/bin/python
from os import path
from sys import argv, exit
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from time import localtime,mktime
from logprint import LogPrint

parser = ArgumentParser(description = 'Collect history data from selected items')
parser.add_argument('--url', required = True, dest = 'url', help = 'Zabbix server address')
parser.add_argument('--user', required = True, dest = 'user', help = 'Zabbix user')
parser.add_argument('--password', required = True, dest = 'password', help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Dont show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--group', required = True, dest = 'group', help = 'Hostgroup name with hosts to look for')
parser.add_argument('--item', required = True, dest = 'item', help = 'Item name inside each host of hostgroup')
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
args = parser.parse_args()

TIMEOUT = 15.0
LOGFILE = "/tmp/%s.log" % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())

try:
    zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
    zapi.login(args.user,args.password)
except Exception, e:
    logger.error("Unable to login: %s" % (e))
    exit(1)

groupids = zapi.hostgroup.get(output=['groupid'],search={'name': args.group })

itens = zapi.item.get(output=['name','itemid','value_type','delay'],groupids=[x['groupid'] for x in groupids],
    search={'name': args.item },filter={'status': 0, 'state': 0},
    selectHosts=['name'],sortorder='ASC',sortfield='itemid')
value_type = itens[0]['value_type']
time_from = mktime(localtime()) - int(itens[0]['delay']) - 15

history = zapi.history.get(output='extend',history=value_type,itemids=[x['itemid'] for x in itens],
    time_from=time_from)

def get_last_history(itemid,history):
    lastclock = int(0)
    for h in history:
        if h['itemid'] == itemid and lastclock == 0:
            value = h['value']
            lastclock = h['clock']
        elif h['itemid'] == itemid and h['clock'] > lastclock:
            value = h['value']
            lastclock = h['clock']
    return { 'value': value, 'clock': lastclock }


for item in itens:
    x = get_last_history(item['itemid'],history)
    logger.info("Host {0}, itemid {1}, value {2}, clock {3}".format(item['hosts'][0]['name'],item['itemid'],x['value'],x['clock']))

logger.info("Fim")
zapi.user.logout()
