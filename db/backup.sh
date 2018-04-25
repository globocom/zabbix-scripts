#!/bin/bash
#
# zabbix-mysql-backupconf.sh
# v0.6 - 20161122 Find out what tables exist and copy them all, except known
#                 data tables; they are structure copied only. This is most
#                 useful between Zabbix versions.
# v0.5 - 20160416 Support migrated to 3.0, auth into database moved
#                 to --default-extra-file
#                 Changed from user/pass to extra-file auth method
# v0.4 - 20120302 Incorporated mysqldump options suggested by Jonathan Bayer
# v0.3 - 20120206 Backup of Zabbix 1.9.x / 2.0.0, removed unnecessary use of
#                 variables (DATEBIN etc) for commands that use to be in $PATH
# v0.2 - 20111105
#
# Configuration Backup for Zabbix 2.0+ w/MySQL
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
EXTRADIR='/opt/zabbix_keys/db'
EXTRAFILE="${EXTRADIR}/${DBHOST}"
DBNAME="$2"
# following will store the backup in a subdirectory of the current directory
MAINDIR="`dirname \"$0\"`"
DUMPDIR="/opt/zabbix/backup/${DBHOST}/`date +%Y%m%d-%H%M`"
TMPDIR="/dev/shm"

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

# tables with large data
DATATABLES=( acknowledges alerts auditlog auditlog_details events event_recovery event_tag \ 
history history_log history_str history_text history_uint housekeeper \ 
problem problem_tag sessions trends trends_uint )

DUMPFILE="${DUMPDIR}/zbx-conf-bkup-`date +%Y%m%d-%H%M`.sql.gz"
DUMPFILETMP="${TMPDIR}/zbx-conf-bkup-`date +%Y%m%d-%H%M`.sql"
[ ! -f "${DUMPDIR}" ] && mkdir -p "${DUMPDIR}"
>"${DUMPFILETMP}"
>"${DUMPFILE}"

TABLES=`mysql --defaults-extra-file=${EXTRAFILE} ${DBNAME} -e 'show tables;' | tail -n +2`
# configtables, loop through all tables and copy them..
for table in ${TABLES}; do
	found=0; # ignore large tables like history and stuff
	for x in ${DATATABLES[*]}; do
		[ "$x" == "$table" ] && found=1;
	done
	[ $found -eq 1 ] && continue;
	echo "Backuping config table ${table}"
	mysqldump --defaults-extra-file=${EXTRAFILE} --set-gtid-purged=OFF \
		${DBNAME} --tables ${table} >>"${DUMPFILETMP}"
done

# datatables, with history we dont need
for table in ${DATATABLES[*]}; do
		echo "Backuping data table ${table}"
		mysqldump --defaults-extra-file=${EXTRAFILE} --set-gtid-purged=OFF \
			--no-data ${DBNAME} --tables ${table} >>"${DUMPFILETMP}"
done

echo "Compressing file"
gzip -c "${DUMPFILETMP}" > "${DUMPFILE}"
rm "${DUMPFILETMP}"

echo
echo "Backup Completed - ${DUMPDIR}"
#echo "Hit ENTER"
#read
