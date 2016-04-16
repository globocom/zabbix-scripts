#!/usr/bin/python
import re
import commands
import string
from os import path
from sys import argv, exit
from datetime import datetime
from pyzabbix import ZabbixAPI, ZabbixAPIException
from argparse import ArgumentParser
from progressbar import ProgressBar, Percentage, ETA, ReverseBar, RotatingMarker, Timer
from logprint import LogPrint

parser = ArgumentParser(description = 'Script used to remove hosts older than --max-age days from hostgroup _DELETED_ (hostgroupid=72)')
parser.add_argument('--url', dest = 'url', required=True, help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', required=True, help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', required=True, help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Dont show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=True)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
parser.add_argument('--max-age', dest = 'max_age', default = 31, help = 'Max age in days for host to be in there')
parser.add_argument('--no-run', dest = 'run', action = 'store_false', help = 'Dont remove any host, just count')
parser.add_argument('--run', dest = 'run', action = 'store_true', help = 'Remove all hosts that expired')
parser.add_argument('--no-matches', dest = 'matches', action = 'store_false', help = 'Dont remove any host that has no prefix')
parser.add_argument('--matches', dest = 'matches', action = 'store_true', help = 'Remove all hosts that has no prefix')
args = parser.parse_args()

TIMEOUT = 30.0
LOGFILE = "/tmp/%s.log" % path.basename(argv[0])
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())

try:
	zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
	zapi.login(args.user,args.password)
except Exception, e:
	logger.error("Unable to login: %s" % (e))
	exit(1)

call = {
		"output": [ "name", "hostid", ],
		"groupids": [ 72 ],
}
hosts = zapi.host.get(**call)
hosts_exclude = []
hosts_no_match = []
date_curr = datetime.now()

"""
Find all hosts that match the expired period
"""
for host in hosts:
	matchObj = re.search( r'_(\d{6})\d+_', host['name'], re.M|re.I)
	if matchObj:
		host_date = datetime.strptime('20%d' % int(matchObj.group(1)), '%Y%m%d')
		timediff = (date_curr - host_date).days
		if ( timediff >= int(args.max_age) ):
			host['timediff'] = timediff
			hosts_exclude.append(host)
	else:
		logger.debug("No matches for host: %s" % host)
		hosts_no_match.append(host)



"""
Perform (or not >> --no-run) the removal of preveously identified hosts
"""
total = hosts_exclude.__len__()
logger.info("Hosts to remove: %d" % total)
if args.run and total > 0:
	x = 0
	bar = ProgressBar(maxval=total,widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
	logger.echo = False
	for host in hosts_exclude:
		x += 1
		bar.update(x)
		logger.debug("(%d/%d) >> Removing >> %s" % (x, total, host))
		out = zapi.host.delete(host['hostid'])
	bar.finish()
	logger.echo = args.verbose

total = hosts_no_match.__len__()
logger.info("Other hosts without timestamp to remove: %d" % total)
if args.run and total > 0 and args.matches:
	x = 0
	bar = ProgressBar(maxval=total,widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
	logger.echo = False
	for host in hosts_no_match:
		x += 1
		bar.update(x)
		logger.debug("(%d/%d) >> Removing >> %s" % (x, total, host))
		out = zapi.host.delete(host['hostid'])
	bar.finish()
	logger.echo = args.verbose

if args.run:
	exit(0)

logger.warning("Not removing.. script ran with --no-run")
zapi.user.logout()
exit(0)
