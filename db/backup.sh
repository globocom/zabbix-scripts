#!/bin/bash
#
# zabbix-mysql-backupconf.sh
# v0.5 - 20160416 Support migrated to 3.0, auth into database moved 
#                 to --default-extra-file
# v0.4 - 20120302 Incorporated mysqldump options suggested by Jonathan Bayer
# v0.3 - 20120206 Backup of Zabbix 1.9.x / 2.0.0, removed unnecessary use of
#                 variables (DATEBIN etc) for commands that use to be in $PATH
# v0.2 - 20111105
#
# Configuration Backup for Zabbix 2.0 w/MySQL
#
# Original author: Ricardo Santos (rsantos at gmail.com)
# http://zabbixzone.com/zabbix/backuping-only-the-zabbix-configuration/
#
# modified by Jens Berthold, 2012
#
# Thanks for suggestions from:
# - Oleksiy Zagorskyi (zalex)
# - Petr Jendrejovsky
# - Jonathan Bayer
#

#
# mysql config
#
DBHOST="$1"
EXTRADIR='/opt/zabbix_keys/db' # Directory for keys for --mysqldump
EXTRAFILE="${EXTRADIR}/${DBHOST}" # File for server should be the name of database, exactly
DBNAME="$2"
# following will store the backup in a subdirectory of the current directory
MAINDIR="`dirname \"$0\"`"
DUMPDIR="/opt/zabbix_bkp/${DBHOST}/`date +%Y%m%d-%H%M`"

usage(){
	echo "backup.sh DBHOST DBNAME"
	echo "note: DBHOST must be a filename inside ${EXTRADIR}"
}

if [ ! -x /usr/bin/mysqldump ]; then
	echo "mysqldump not found."
	exit 1
fi
if [ ! -f $EXTRAFILE ] || [ "x$EXTRAFILE" == 'x' ]; then
	echo "extrafile not found."
	usage
	exit 1
fi

mkdir -p "${DUMPDIR}"

# configuration tables 3.0
CONFTABLES=( actions application_discovery application_prototype application_template applications \ 
autoreg_host conditions config dbversion dchecks dhosts drules dservices escalations expressions functions 
globalmacro globalvars graph_discovery graph_theme graphs graphs_items group_discovery group_prototype \ 
groups host_discovery host_inventory hostmacro hosts hosts_groups hosts_templates httpstep httpstepitem \ 
httptest httptestitem icon_map icon_mapping ids images interface interface_discovery item_condition \ 
item_discovery items items_applications item_application_prototype maintenances maintenances_groups \ 
maintenances_hosts maintenances_windows mappings media media_type opcommand opcommand_grp opcommand_hst \ 
opconditions operations opgroup opinventory opmessage opmessage_grp opmessage_usr optemplate profiles \ 
proxy_autoreg_host proxy_dhistory proxy_history regexps rights screens screens_items screen_user \ 
screen_usrgrp scripts service_alarms services services_links services_times slides slideshows \ 
slideshow_user slideshow_usrgrp sysmap_element_url sysmap_url sysmaps sysmaps_elements \ 
sysmaps_link_triggers sysmaps_links sysmap_user sysmap_usrgrp timeperiods \ 
trigger_depends trigger_discovery triggers users users_groups usrgrp valuemaps )

# tables with large data
DATATABLES=( acknowledges alerts auditlog_details auditlog events \
history history_log history_str history_text history_uint housekeeper sessions trends trends_uint )

DUMPFILE="${DUMPDIR}/zbx-conf-bkup-`date +%Y%m%d-%H%M`.sql.gz"
DUMPFILETMP="/dev/shm/zbx-conf-bkup-`date +%Y%m%d-%H%M`.sql"
>"${DUMPFILETMP}"
>"${DUMPFILE}"

# CONFTABLES
for table in ${CONFTABLES[*]}; do
		echo "Backuping configuration table ${table}"
		mysqldump --defaults-extra-file=${EXTRAFILE} \
			${DBNAME} --tables ${table} >>"${DUMPFILETMP}"
done

# DATATABLES
for table in ${DATATABLES[*]}; do
		echo "Backuping data table ${table}"
		mysqldump --defaults-extra-file=${EXTRAFILE} \
			--no-data ${DBNAME} --tables ${table} >>"${DUMPFILETMP}"
done

echo "Compressing file"
gzip -c "${DUMPFILETMP}" > "${DUMPFILE}"
rm "${DUMPFILETMP}"

echo
echo "Backup Completed - ${DUMPDIR}"
