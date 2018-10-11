#!/usr/bin/python
# Copyright (c) 2016, Globo.com <https://github.com/globocom>
# This file is part of globocom/zabbix-scripts
# (see https://github.com/globocom/zabbix-scripts).
# License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
from os import path
from sys import argv, exit
from logprint import LogPrint
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from progressbar import ProgressBar, Percentage, ETA, ReverseBar, RotatingMarker, Timer

parser = ArgumentParser(description = 'This script removes all hosts from a given hostgroup id. It can also remove a host by its name.')
parser.add_argument('--url', dest = 'url', required = True, help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', required = True, help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', required = True, help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Don\'t show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
parser.add_argument('--hostname', dest = 'hostname', help = 'Host name to be removed')
parser.add_argument('--groupname', dest = 'groupname', help = 'Hostgroup name to be cleaned (all hosts DELETED)! USE WITH CAUTION')
parser.add_argument('--no-run', dest = 'run', action = 'store_false', help = 'Don\'t remove anything, just count (works only with hostgroup)')
parser.add_argument('--run', dest = 'run', action = 'store_true', help = 'Remove every match (works only with hostgroup)')

args = parser.parse_args()

TIMEOUT = 30.0
LOGFILE = "/tmp/%s.log" % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())

if not args.hostname and not args.groupname:
    logger.error('You MUST use at least one of --hostname or --groupname.')
    exit(1)

try:
    zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
    zapi.login(args.user,args.password)
except Exception, e:
    logger.error("Unable to login: %s" % (e))
    exit(1)

def deleteHostByName(hostname):
    logger.print_json(zapi.globo.deleteMonitors(host=hostname))
    return

def deleteHostsByHostgroup(groupname):
    hostgroup = zapi.hostgroup.get(output=['groupid'],filter={'name': groupname})
    if hostgroup.__len__() != 1:
        logger.error('Hostgroup not found: %s\n\tFound this: %s' % (groupname,hostgroup))
    groupid = int(hostgroup[0]['groupid'])
    hosts = zapi.host.get(output=['name','hostid'],groupids=groupid)
    total = len(hosts)
    logger.info('Hosts found: %d' % (total))
    if ( args.run ):
        x = 0
        bar = ProgressBar(maxval=total,widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
        logger.echo = False
        for host in hosts:
            x = x + 1
            bar.update(x)
            logger.debug('(%d/%d) >> Removing >> %s' % (x, total, host))
            out = zapi.globo.deleteMonitors(host['name'])
        bar.finish()
        logger.echo = True
    else:
        logger.info('No host removed due to --no-run arg. Full list of hosts:')
        for host in hosts:
            logger.info('%s' % host['name'])
    return


if ( args.hostname ):
    deleteHostByName(hostname=args.hostname)
    exit(0)

if ( args.groupname ):
    deleteHostsByHostgroup(groupname=args.groupname)
    exit(0)
zapi.user.logout()
