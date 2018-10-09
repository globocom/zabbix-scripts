#!/bin/env python
#from __future__ import print_function
"""
Copyright (c) 2018.
This file is part of globocom/zabbix-scripts
(see https://github.com/globocom/zabbix-scripts).
License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
"""
import pymysql,sys,os,json
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from logprint import LogPrint
from progressbar import ProgressBar, Percentage, ETA, ReverseBar, RotatingMarker, Timer

parser=ArgumentParser(description='Script to copy items history from one database to another')
parser.add_argument('--url',dest='url',help='Zabbix frontend address')
parser.add_argument('--zuser',dest='zabbixuser',help='Zabbix frontend user')
parser.add_argument('--zpassword',dest='zabbixpassword',help='Zabbix frontend password')

parser.add_argument('--dbuser',dest='dbuser',help='Database user')
parser.add_argument('--dbpassword',dest='dbpassword',help='Database password')
parser.add_argument('--dbbkphost',dest='dbbkphost',help='Backup database to get trends data from')
parser.add_argument('--dblivehost',dest='dblivehost',help='Production database to get items from')

parser.add_argument('--no-verbose',dest='verbose',action='store_false',help='Don\'t show any logs on screen')
parser.add_argument('--verbose',dest='verbose',action='store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel',dest='loglevel',default='ERROR',help='Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
args=parser.parse_args()
tmp_dir='../tmp'
move_items_file='%s/move_items.txt' % tmp_dir

TIMEOUT=30.0
LOGFILE='/tmp/%s.log' % os.path.basename(sys.argv[0])
logger=LogPrint(echo=args.verbose,logfile=LOGFILE,loglevel=args.loglevel.upper())
# Connects to zabbix api to get hostid's,verify itemid's and item type (maybe?)
try:
	zapi=ZabbixAPI(args.url,timeout=TIMEOUT)
	zapi.login(args.zabbixuser,args.zabbixpassword)
except Exception,e:
	logger.error('Unable to login to Zabbix: %s' % (e))
	sys.exit(1)

if not os.path.exists(tmp_dir):
	os.makedirs(tmp_dir)

# Connects to production database (read and write)
try:
	dblive=pymysql.connect(host=args.dblivehost,port=3306,user=args.dbuser,passwd=args.dbpassword,db='zabbix_staging')
except Exception,e:
	logger.error('Unable to login to LIVE database (%s): %s' % (args.dblivehost,e))
	sys.exit(1)

# Connection to backup database,where our backup history lies
try:
	dbbkp=pymysql.connect(host=args.dbbkphost,port=3306,user=args.dbuser,passwd=args.dbpassword,db='zabbix')
except Exception,e:
	logger.error('Unable to login to BACKUP database (%s): %s' % (args.dbbkphost,e))
	sys.exit(1)

def getItems(hostgroups=['138']):
	'''
	Search for all hosts inside hostgroups
	Identify all items present in both production and bkp databases

	[{"hostid": "17906", "itens": [
		{"itemid": 3663516, "status": 0, "value_type": 3, "bkpitemid": 3409700, "key_": "ltmNodeAddrStatServerCurConns[/Common/1.1.1.1,15.47.67.111.109.109.111.110.47.49.46.49.46.49.46.49]"}, 
		{"itemid": 3663517, "status": 0, "value_type": 3, "bkpitemid": 3409701, "key_": "ltmNodeAddrStatServerCurConns[/Common/10.1.1.1,16.47.67.111.109.109.111.110.47.49.48.46.49.46.49.46.49]"
	],
	"name": "HOST"}
	},
	'''
	logger.info('Discovering hostid\'s and item\'s')
	# Get hostid's from Zabbix
	hosts=zapi.host.get(output=['hostid','name'],groupids=hostgroups)

	live={}
	bkp={}
	for host in hosts:
		logger.debug('Working on host: %s' % host)
		# When changing this select order or results, remember to do the same for the lists on 'for item'
		itemsQuery='SELECT itemid,key_,status,value_type FROM items WHERE hostid=%d and (key_ LIKE \"ltmNodeAddr%s\" OR key_ LIKE \"ltmNodeAddr%s\" OR key_ LIKE \"ltmVirtualServStatClient%s\" OR key_ LIKE \"ltmVsStatusAvailState%s\")' % (int(host['hostid']),'%','%','%','%')
		curdblive.execute(itemsQuery)
		curdbbkp.execute(itemsQuery)
		live['mysql_items']=curdblive.fetchall()
		bkp['mysql_items']=curdbbkp.fetchall()

		if live['mysql_items'].__len__() != bkp['mysql_items'].__len__():
			logger.warning('Different number of items on prod and backup:')
			logger.warning('mysql results for live: %d' % live['mysql_items'].__len__())
			logger.warning('mysql results for backup: %d' % bkp['mysql_items'].__len__())

		host['itens']=[]
		# For each current item, we find if there's any match on backup and list it here
		for item in live['mysql_items']:
			# Search for the match!
			for bkpitem in bkp['mysql_items']:
				if bkpitem[1] == item[1] and bkpitem[2] == item[2] and bkpitem[3] == item[3]:
					break
			# Create this host item match list
			host['itens'].append({'itemid': item[0], 'key_': item[1], 'status': item[2], 'value_type': item[3], 'bkpitemid': bkpitem[0]})
	logger.info('Hostid\'s and item\'s discovered.')
	return hosts

def getTrends(hostname,item):
	'''
	Get trends data for a given itemid
	Returns a list like this
	(3409700, 1440356400, 6, 0, 0, 0)
	'''
	logger.debug('Geting trends data: %s:%s' % (hostname,item['key_']))
	values={}
	if item['value_type'] == 3:
		values['table']='trends_uint'
	elif item['value_type'] == 0:
		values['table']='trends'
	valuesQuery='SELECT itemid,clock,num,value_min,value_avg,value_max FROM %s WHERE itemid=\'%d\'' % (values['table'],int(item['bkpitemid']))
	curdbbkp.execute(valuesQuery)
	values['values']=curdbbkp.fetchall()
	return values
def createSQL(table,values,name='insert'):
	'''
	Generate the SQL insert line, breaking each insert to up to ~1k values
	and up to ~1k insert's (~1M values total for each SQL file)
	'''
	logger.info('Generating SQL file')
	queryInsert='INSERT INTO %s (itemid,clock,num,value_min,value_avg,value_max) VALUES' % table
	i=0 # Controls the progress bar
	x=0 # Controls number of inserts in one line
	y=0 # Controls number of lines in one file
	z=0 # Controls number of file name
	valuesLen=values.__len__()
	sqlFile='%s.sql.%d' % (name,z)
	logger.debug('Total itens for %s: %d' % (name,valuesLen))

	if valuesLen > 0:
		bar=ProgressBar(maxval=valuesLen,widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
		for value in values:
			i+=1
			x+=1
			if x != 1: # First line only
				sqlInsert='%s,%s' % (sqlInsert,value)
			else:
				sqlInsert=value
			if y >= 1000: # If there is more than 1k lines, write to new file
				z+=1
				y=0
			if x >= 1000 or i == valuesLen: # If there is more than 1k values or we finished our list, write to file
				sqlFile='%s.sql.%d' % (name,z)
				fileAppend(f=sqlFile,content='%s %s;\n' % (queryInsert,sqlInsert))
				x=0
				y+=1
				sqlInsert=''
			if args.loglevel.upper() != 'DEBUG': # Dont print progressbar if in debug mode
				bar.update(i)
		bar.finish()
	else:
		logger.warning('No values received')
def fileAppend(f=None,content=None):
	'''
	Adds content to a given file
	'''
	if not (f and content):
		logger.warning('Error when writing new file: no data received')
		return False
	f='%s/%s' % (tmp_dir,f)
	with open(f,'a') as f:
		f.write(content)
		return True
def main():
	'''
	Controls general flow of operations
	'''
	# If it exists, use the cached data of hosts and items
	if (os.path.isfile(move_items_file)):
		with open(move_items_file) as infile:
			hosts=json.load(infile)
			logger.info('Cache loaded from file (%s)' % move_items_file)
	else:
		hosts=getItems()
		with open(move_items_file, 'w') as outfile:
			json.dump(hosts, outfile)
			logger.info('Cache written to file (%s)' % move_items_file)

	for host in hosts:
		logger.info('Geting trends data of host: %s' % host['name'])
		host['trends']=list()
		host['trends_uint']=list()
		if host['itens'].__len__() > 0:
			bar=ProgressBar(maxval=host['itens'].__len__(),widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
			i=0
			for item in host['itens']:
				temp=getTrends(hostname=host['name'],item=item)
				i+=1
				if args.loglevel.upper() != 'DEBUG':
					bar.update(i)
				if temp['table'] == 'trends':
					for value in temp['values']:
						host['trends'].append('(%d, %d, %d, %d, %d, %d)' % (int(item['itemid']), int(value[1]), int(value[2]), int(value[3]), int(value[4]), int(value[5])))
				elif temp['table'] == 'trends_uint':
					for value in temp['values']:
						host['trends_uint'].append('(%d, %d, %d, %d, %d, %d)' % (int(item['itemid']), int(value[1]), int(value[2]), int(value[3]), int(value[4]), int(value[5])))
				else:
					logger.warning('Unknown value type: %s' % temp['table'])
			bar.finish()
		'''
		Now, we send in blocks of up to ~1M values to generate the SQL files
		'''
		if host['trends'].__len__() > 0:
			createSQL(table='trends',values=host['trends'],name=host['name'])
		elif host['trends_uint'].__len__() > 0:
			createSQL(table='trends_uint',values=host['trends_uint'],name=host['name'])
		else:
			logger.warning('No data from %s found to be sent.' % host['name'])



# Start DB connection
curdblive=dblive.cursor()
curdbbkp=dbbkp.cursor()
main()

