#!/usr/bin/python
from socket import gethostbyname
from types import DictType
from sys import exit
from pyzabbix import ZabbixAPI
from argparse import ArgumentParser
from subprocess import Popen, PIPE # For zabbix reload
from netaddr import IPNetwork, IPAddress # For matching ip and network
from logprint import LogPrint
from netdiscovery import NetworkGet

parser = ArgumentParser(description = 'Create discovery rules for all necessary networks for Globo.com')
parser.add_argument('--url', dest = 'url', required = True, help = 'Zabbix server address')
parser.add_argument('--user', dest = 'user', required = True, help = 'Zabbix user')
parser.add_argument('--password', dest = 'password', required = True, help = 'Zabbix password')
parser.add_argument('--no-verbose', dest = 'verbose', action = 'store_false', help = 'Don\'t show any logs on screen')
parser.add_argument('--verbose', dest = 'verbose', action = 'store_true')
parser.set_defaults(verbose=False)
parser.add_argument('--loglevel', dest = 'loglevel', default = 'ERROR', help = 'Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL')
parser.add_argument('--fake', dest = 'fake', default = 0, help = 'Just fake the execution and simulate the result (BETA)')
parser.add_argument('--no-move', dest = 'move', action = 'store_false', help = 'Manage only new vlans. Existing ones will not be moved between proxies (Better)')
parser.add_argument('--move', dest = 'move', action = 'store_true')
parser.set_defaults(move=False)

# CUSTOM VARIABLES
TIMEOUT = 30.0 #ZabbixAPI timeout
# Grupos excluidos de operacoes no zabbix, de discovery
forbiden_groups = ( '_DELETED', 'Cloud', 'Template', 'Zabbix' )
# Redes que sao removidas forcadamente. Nao ha discovery automatico dessas, abaixo
networks_blacklist = {}
networks_blacklist['rj'] = [ '10.0.0.0/16' ]
networks_blacklist['sp'] = [ '10.1.0.0/16' ]
DNS_SUFIX = 'suaempresa.com' # Concatenado nas buscas de ip/dns
ZABBIX_SERVERS = {
	'http://zabbix.suaempresa.com' : [ '10.0.1.1', '10.0.1.2' ],
	'http://zabbix2.suaempresa.com' : [ 'localhost' ],
}

# OTHER VARIABLES
args = parser.parse_args()
fake = args.fake
LOGFILE = '/tmp/zbx_discovery-manager.log'
logger = LogPrint(echo=args.verbose, logfile=LOGFILE, loglevel=args.loglevel.upper())
loglevels = {
	'CRITICAL'	: 50,
	'ERROR' 	: 40,
	'WARNING'	: 30,
	'INFO'		: 20,
	'DEBUG'		: 10
}

try:
	zapi = ZabbixAPI(args.url,timeout=TIMEOUT)
	zapi.login(args.user,args.password)
except Exception, e:
	logger.error('Unable to login: {0}'.format(e))
	exit(1)

# CUSTOM FUNCTIONS
def discovery_checks():
	"""
	retornar o formato json com os discovery checks
	essa entrada eh manual
	"""
	dchecks = [
		{ 'uniq': '1', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'sysName.0' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'sysDescr.0' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'sysContact.0' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'MIB-Dell-10892::chassisModelName.1' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'LSI-MegaRAID-SAS-MIB::productName.0' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'F5-BIGIP-SYSTEM-MIB::sysProductName.0' },
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'ENTITY-MIB::entPhysicalAlias.155',},
		{ 'uniq': '0', 'snmp_community': '{$SNMP_COMMUNITY}', 'type': '11', 'ports': '161', 'key_': 'CPQSINFO-MIB::cpqSiProductName.0', },
	]
	return dchecks
def discovery_rule(ip_range,proxy_hostid,proxy_name):
	"""
	criar/atualizar a regra dentro do zabbix, passando apenas o range de ip
	ignora o primeiro ip e os 2 ultimos
	aceita de /19 ate /32
	"""
	rule_name = 'SNMP_auto - {0}'.format(ip_range)
	ip = IPNetwork(ip_range)
	ip_list = list(ip)
	ip_range_small = ''
	if ip.prefixlen >= 30:
		ip_range_small = ip_range
	elif ip.prefixlen >= 24 and ip.prefixlen < 30:
		ip_range_small = '{0}-{1}'.format(str(ip_list[2]), str(ip_list[-4]).split('.')[3])
	elif ip.prefixlen > 18 and ip.prefixlen < 24:
		nets = list(ip.subnet(24))
		for index in range(nets.__len__()):
			ip_list = list(IPNetwork(nets[index]))
			if index == 0: # Primeiro
				ip_range_small = '{0}-{1}'.format(str(ip_list[2]), str(ip_list[-1]).split('.')[3])
			elif index == (nets.__len__()-1): # Ultimo
				ip_range_small = '{0},{1}-{2}'.format(ip_range_small,str(ip_list[2]), str(ip_list[-4]).split('.')[3])
			else: # Do meio
				ip_range_small = '{0},{1}-{2}'.format(ip_range_small,str(ip_list[1]), str(ip_list[-1]).split('.')[3])
	else:
		logger.warning('Tamanho de rede invalido: {0}'.format(ip_range))
	dchecks = discovery_checks()
	out={ 'druleids': 'fake data' }
	exists = zapi.drule.get(output=['name'],filter={'name': rule_name})
	params = { 'name': rule_name, 'iprange': ip_range_small, 'delay': '86400', 'proxy_hostid': proxy_hostid, 'dchecks': dchecks, 'status': 1 }
	if exists.__len__() == 1:
		query = {
			'output':[ 'druleids' ],
			'search': { 'name': rule_name }
		}
		params['druleid'] = zapi.drule.get(**query)[0]['druleid']
		if not args.move:
			del params['proxy_hostid']
		if not fake:
			out = zapi.drule.update(**params)
	elif exists.__len__() == 0:
		# Nao existe a regra de discovery ainda..
		if not fake:
			out = zapi.drule.create(**params) #fecha zapi.drule.create
	else:
		logger.error('Too many discovery rules for {0}: {1}'.format(rule_name,exists.__len__()))

	if ( out or fake ):
		logger.debug('\t{0} --> rule {1} ({2})'.format(proxy_name,rule_name,out['druleids']))
	else:
		logger.error('\tFAILED:\t{0} --> rule {1} ({2})'.format(proxy_name,rule_name,out['druleids']))
	return
def discovery_rule_per_proxy():
	"""
	Distribuo as redes a serem descobertas nos proxies.
	"""
	weight_per_proxy = {}
	for local in network_ranges:
		weight_per_proxy[local] = ( network_ranges[local]['total_weight'] / len(proxies[local]) )
		logger.debug('\tCada proxy do {0} devera ter {1} \'pesos\' de discovery'.format(local,weight_per_proxy[local]))

	# Busco as redes ja existentes e aloco os ranges nos proxies..
	# Ignorarei la na frente esses ranges, para evitar realocacao
	drules_cache = discovery_rules()

	# Marco as redes como usadas, aquelas que ja estao alocadas
	if ( args.move == False):
		for rule in drules_cache:
			local = network_find(rule['iprange'])
			if ( local ):
				network_ranges[local][rule['iprange']]['used'] = True
				for i in proxies[local]:
					if ( i['proxyid'] == rule['proxy_hostid'] ):
						if ( i.get('total_weight', False) ):
							i['total_weight'] += network_ranges[local][rule['iprange']]['weight']
						else:
							i['total_weight'] = network_ranges[local][rule['iprange']]['weight']
						i['ranges'].append(rule['iprange'])
						break

	# Aloco as redes aos proxies com menor peso atribuido
	for local in network_ranges:
		for x in network_ranges[local]:
			if ( (str(x) == 'disabled') or (str(x) == 'total_weight') ):
				continue
			if ( type(network_ranges[local].get(x)) is DictType):
				if ( network_ranges[local].get(x).get('used', False) == True ):
					continue
				tmp_weight = int(network_ranges[local].get(x).get('weight'))
				proxy = proxies_low_weight(local)
				proxy['total_weight'] += tmp_weight
				logger.debug( '{0} --> add network {1} --> weight {2} --> acumulado {3}'.format(proxy['host'],x,tmp_weight,proxy['total_weight']) )
				network_ranges[local].get(x)['used'] = True
				proxy['ranges'].append(x)
		proxies[local].sort(key=lambda d: d['host'])
	return
def proxies_low_weight(local):
	"""
	Retorna o proxyid do proxy com o menor peso atribuido.
	Em caso de empate, a ordem do loop prevalece.
	"""
	proxies[local].sort(key=lambda d: d['total_weight'])
	for proxy in proxies[local]:
		return proxy
def network_find(net):
	"""
	Busco por rede em qualquer local
	Retorno o local
	"""
	for local in network_ranges:
		if ( type(network_ranges[local].get(net)) is DictType ):
			return local
	return False
def discovery_rules():
	"""
	Retorna a lista de discovery rules existentes
	"""
	query = { 'output': 'extend', 'search': { 'name': 'SNMP_auto' } }
	return zapi.drule.get(**query)
def discovery_change_status(status=0):
	"""
	Alterar status de todos os discoveries *auto*
	Status 0 = enable
	Status 1 = disable
	""" 
	dchecks = discovery_checks()
	query = { 'output': [ 'druleid', 'iprange', 'name', 'proxy_hostid', 'status' ], 'search': { 'name': 'SNMP_auto' } }
	druleids = zapi.drule.get(**query)
	for i in druleids:
		if ( int(i['status']) == status ):
			logger.debug('Discovery rule already set at: {0} <==> {1}'.format(i['name'],status))
			continue
		query = {
			'name': i['name'], 'druleid': i['druleid'], 'iprange': i['iprange'], 
			'proxy_hostid': i['proxy_hostid'], 'dchecks': dchecks, 'status': status
		}
		if not fake:
			out = zapi.drule.update(**query)
		if out or fake:
			logger.debug('\tNew status: {0} ({1}) --> {2}'.format(i['name'],out['druleids'],status))
		else:
			logger.warning('\tFAILED to change status: {0} ({1}) --> {2}'.format(i['name'],out['druleids'],status))
def network_api_get_ranges():
	"""
	Conectar na network api e capturar as redes de BE
	-- 'be', 'producao', 'core/densidade'
	"""

	netapi = NetworkGet()
	for local in networks_blacklist:
		for x in networks_blacklist[local]:
			netapi.networks_blacklist[local].append(x)
	netapi.getNetworkAPI()
	return netapi.getNetwork()
def zabbix_server_get():
	"""
	'Descobre' qual o zabbix server do ambiente
	A API nao possui essa informacao
	"""
	if ( args.url in ZABBIX_SERVERS.keys() ):
		return options[args.url]
	else:
		logger.error('ERROR: No zabbix_server know to reload for {0}.'.format(args.url))
def zabbix_server_reload():
	"""
	Efetuar o reload no zabbix server
	Necessario tratar os dois possiveis servers!!!
	"""
	zabbix_servers = zabbix_server_get()
	for zabbix_server in zabbix_servers:
		print 'Reloading zabbix_server on {0}'.format(zabbix_server)
		cmd = 'ssh -l root {0} \'/etc/init.d/zabbix_server reload\''.format(zabbix_server) # Chamo o alias de reload do zabbix_server
		if not fake:
			p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
			out, err = p.communicate()
		if ( (out.rstrip() == 'Reloading Zabbix Server: command sent successfully') or fake ):
			info_message = 'Reloaded: ', out.rstrip()
			info(info_message)
		else:
			break # Por enquanto ignoro os erros.. provavelmente o zbx_server nao esta rodando
			logger.error('ERROR: Failed to reload {0}. Message: {1}'.format(zabbix_server, out.rstrip()))
	return
def proxy_distribute_rules():
	"""
	Pegar os resultados ja quase consolidados e aplica-los
	A lista proxies['ranges'] deve ser considerada, para cada proxy
	Necessario pegar os dados do proxy e range, p/ usar no drule!
	"""
	dchecks = discovery_checks()
	for local in proxies:
		for x in proxies[local]:
			for i in x['ranges']:
				discovery_rule(i,x['proxyid'],x['host'])
def proxies_get():
	"""
	Conectar na API do zabbix e recuperar os proxies (host e proxyid)
	possiveis p/ uso
	"""
	proxies = {}
	proxies_search = {}
	#proxies_search['NOME NO NETDISCOVERY'] = 'NOME DO PROXY NO ZABBIX'
	proxies_search['rj'] = 'RJ'
	proxies_search['sp'] = 'SP'
	proxies_search['rj1'] = 'RJ' # compatibilidade entre nomes
	tmp_proxies = {}
	for local in proxies_search:
		proxies[local] = zapi.proxy.get(output=['host','proxyid'],search={'host': proxies_search[local]},selectHosts='extend')
		tmp_proxies[local] = []
		for proxy in proxies[local]:
			proxy['newhosts'] = list()
			proxy['total_weight'] = 0
			proxy['ranges'] = list()
			if (  '-BE' in proxy['host'] ):
				tmp_proxies[local].append(proxy)
	del proxies,proxies_search
	if ( len(tmp_proxies) > 0 ):
		return tmp_proxies
	else:
		logger.error('\tFAILED: no proxies found, looking for \'{0}\''.format(proxies_search))
def proxy_decide_hosts(ip,hostid,host):
	"""
	Baseado no ip do host informado, decido para qual proxy ele deve ser direcionado
	utilizando o proxies(index)['ranges']
	ip precisa de pelo menos 7 chars (1.1.1.1 = 7)
	"""
	if ( hostid.isspace() or host.isspace() or (len(ip) < 6 )):
		logger.error('Failed on proxy_decide_hosts({0},{1},{2}). Invalid params'.format(ip,hostid,host))
	for local in proxies:
		for x in proxies[local]:
			for y in x['ranges']:
				if IPAddress(ip) in IPNetwork(y):
					logger.debug('ip match found for {0} ==> {1} ==> {2}'.format(x['host'],ip,y))
					x['newhosts'].append(hostid)
					return
	logger.debug('No network found for host {0} with ip {1}'.format(host,ip))
	return
def hosts_get_all():
	"""
	Identificar todos os hosts a serem migrados
	"""
	query = {
		'output': [ 'name', 'host', 'hostid', 'proxy_hostid' ],
		'selectInterfaces': [ 'dns', 'useip', 'ip', 'type', 'main' ],
		'selectGroups': [ 'groupid', 'name' ],
	}
	hosts = zapi.host.get(**query)

	for host in hosts:
		stop = False
		for group in host['groups']:
			for forbiden_group in forbiden_groups:
				if ( forbiden_group in group['name'] ):
					stop = True
					break
		if (stop):
			logger.debug('Grupo {0} nao permitido'.format(group['name']))
			continue

		for interface in host['interfaces']:
			if ( int(interface['main']) == 1 ):
				if ( int(interface['useip']) == 1): #Se for por IP
					ip = interface['ip']
				else: #Se for por DNS, descubro qual o IP
					if ( DNS_SUFIX in interface['dns'] ):
						dns = interface['dns']
					elif ('localhost' in interface['dns']):
						dns = 'localhost'
					else:
						dns = interface['dns'] + DNS_SUFIX
					
					# Como nao sei qual o ip, resolvo para poder decidir que rede usar
					if ( (dns) and (dns != DNS_SUFIX) ):
						try:
							ip = gethostbyname(dns)
						except:
							logger.print_json(host)
							logger.debug('Could not resolv {0}'.format(dns))
							stop = True
							break
					else:
						logger.print_json(host)
						logger.debug('Could not determine the dns correctly')
						stop = True
						break
				if ( (IPAddress(ip) in IPNetwork('127.0.0.1/8')) or (IPAddress(ip) in IPNetwork('10.31.0.0/24')) ):
					stop = True
					logger.debug('IP {0} nao permitido'.format(ip))
				break
		if ( not stop ):
			proxy_decide_hosts(ip, host['hostid'], host['host'])
def hosts_to_proxies():
	"""
	Mover os hosts em proxies[proxy]['newhosts'] para o novo proxy
	Usar massupdate p/ isso, isso eh CRITICO
	Caso contrario podemos perder relacionamento de host com proxy
	ou perder muita performance
	"""
	for local in proxies:
		for proxy in proxies[local]:
			out = { 'newhosts': 'fake data' }
			if not fake:
				query = {
					'proxy_hostid': proxy['proxyid'],
					'hosts': [ { 'hostid': x } for x in proxy['newhosts'] ]
				}
				out = zapi.host.massupdate(**query)
			if out or fake:
				logger.debug('\tSUCCESS: updated proxy with {0} hosts: {1}'.format(len(proxy['newhosts']),proxy['host']))
				if ( loglevels[args.loglevel.upper()] < loglevels['INFO'] ):
					logger.debug('Detailed hosts at proxy {0}'.format(proxy['host']))
					logger.print_json(out)
			else:
				logger.warning('\tFAILED: updated proxy with {0} hosts: {1}'.format(len(proxy['newhosts']),proxy['host']))

#1) Identificar redes via network api
logger.info('1) Descobrir as redes:')
network_ranges = network_api_get_ranges()
for local in network_ranges:
	logger.info('Achei {0} redes para {1}'.format((len(network_ranges[local]) -2),local) ) # diminuo dois para ignorar o disabled e total_weight

#2) Identificar proxies disponiveis
logger.info('2) Descobrir os proxies cadastrados:')
proxies = proxies_get()
for local in proxies:
	#logger.print_json(proxies[local])
	logger.info('Achei {0} proxies para {1}'.format(len(proxies[local]),local))

#2.1) Calcular a distribuicao das redes por proxy
#2.2) Atribuir peso de quantidade maxima de hosts por rede, e calcular assim por proxy
discovery_rule_per_proxy()
logger.debug('2.1) Total de ranges por proxy:')
if ( loglevels[args.loglevel.upper()] < loglevels['INFO'] ):
	for local in proxies:
		for x in proxies[local]:
			logger.debug('\tRanges p/ {0} = {1}'.format(x['host'],len(x['ranges'])))

#3) Distribuir de fato os discoveries nos proxies
logger.info('3) Realocar e desabilitar todas as regras de discovery para os proxies')
proxy_distribute_rules()

#4) Identificar os hosts que devem ser migrados de proxy
logger.info('4) Identificar os hosts que devem ser migrados de proxy')
if ( args.move ):
	hosts_get_all()
else:
	logger.info('\t--no-move utilizado. Nao necessario.')

#5) Migrar esses hosts
logger.info('5) Migrar esses hosts')
if ( args.move ):
	hosts_to_proxies()
else:
	logger.info('\t--no-move utilizado. Nao necessario.')

#6) Sync dos dados (reload)
logger.info('6) Reload zabbix server e esperar pelo sync dos proxies')
logger.info('\tfuncao desligada')
#zabbix_server_reload()

#7) Ativar os discoveries
logger.info('7) Ativar todos os discoveries')
discovery_change_status(0)

#8) Mostrar resumo dos pesos dos proxies
logger.info('8) Resumo dos proxies')
logger.info('\tLocal || Proxy\t\t|| Redes || Peso')
for local in proxies:
	for prx in proxies[local]:
		logger.info('\t{0} || {1} || {2} || {3}'.format(local,prx['host'],len(prx['ranges']),prx['total_weight']))

#9) Finish!
logger.debug('finished.. debug log')
logger.print_json(proxies)

logger.info('Terminei.. gastei alguns segundos preciosos..')
zapi.user.logout()
exit(0)
