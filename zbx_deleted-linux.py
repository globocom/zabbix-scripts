#!/usr/bin/python
"""
Copyright (c) 2018.
This file is part of globocom/zabbix-scripts
(see https://github.com/globocom/zabbix-scripts).
License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
"""
import commands
import string
from os import path
from sys import argv, exit
from logprint import LogPrint
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser

parser = ArgumentParser(description = 'This script connects to each server that looks like LINUX and stops its snmpd, preventing removed hosts from beeing rediscovered.')
parser.add_argument('--url', dest = 'url', help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Dont show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
parser.add_argument('--sshkey', dest = 'sshkey', help = 'SSH Key to be used')
parser.add_argument('--groupid', dest = 'groupid', default = '72', help = 'Groupid to be checked. Default: 72')
args = parser.parse_args()

LOGFILE = "/tmp/%s.log" % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())
try:
	zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
	zapi.login(args.user,args.password)
except Exception, e:
	logger.error("Unable to login: %s" % (e))
	exit(1)

# Filtra do hostgroup _DELETED_ os hosts com status 0.
a = zapi.host.get(groupids=[ args.groupid ],selectInterfaces='extend',output=['name','hostid'],filter={"status": 0})
#,templateids=['10069'])

for host in a:
	logger.debug("Doing host %s" % host['name'])
	ok = 0
	for ip in host['interfaces']:
		if ip['main'] == '1':
			zapi.host.update(hostid=host['hostid'],status=1)
			# Verifico se pareco linux. Poderia verificar pelo template... Mas ai seriam multiplas buscas
			if ( 'lf' in host['name'] or 'ls' in host['name'] or 'lb' in host['name'] ):
				if args.sshkey:
					exe = "ssh -i %s root@%s \"/etc/init.d/snmpd stop\"" % (ip['ip'],args.sshkey)
				else:
					exe = "ssh root@%s \"/etc/init.d/snmpd stop\"" % (ip['ip'])
				(status,out) = commands.getstatusoutput(exe)
				logger.warning("Failed on %s" % ip['ip'])
	if ok == 0:
		logger.warning("Failed for %s" % host['name'])
zapi.user.logout()
