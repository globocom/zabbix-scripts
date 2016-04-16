#!/bin/sh


DBHOST="$1"
EXTRADIR='/mnt/projetos/deploy-be/zabbix_keys/db'
EXTRAFILE="${EXTRADIR}/${DBHOST}"
DBNAME="$2"
usage() {
  echo "import.sh DBHOST DBNAME"
  echo "note: DBHOST must be a filename inside ${EXTRADIR}"
}
if [ ! -r "${EXTRAFILE}" ]; then
  echo "no extra-file found at ${EXTRADIR}"
  usage
  exit 1;
fi
if [ "x${DBNAME}" == "x" ]; then
  echo "no database name found"
  usage
  exit 1;
fi
date;
path="/opt/zabbix_backup/zabbix/master.database.suaempresa.com/";
i=`ls $path|tail -n1`;
echo "Found $i. Coping to curr dir..";
sql="zbx-conf-bkup-${i}.sql";
cd /dev/shm;
cp ${path}/${i}/${sql}.gz .;
[ ! -f "${sql}" ] && echo "Ungziping.." && gzip -d ${sql}.gz;
if [ -f "${sql}" ]; then
  echo "Cleaning target database"
  DEL=`echo "select '/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;' union select concat('drop table ',table_schema,'.',table_name,';') from information_schema.tables where table_schema = '$DBNAME' union select '/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;'" | mysql --defaults-extra-file=${EXTRAFILE};`;
  time mysql --defaults-extra-file=${EXTRAFILE} ${DBNAME} -e "$DEL";
  echo "Importing to mysql database ${db}..";
  time mysql --defaults-extra-file=${EXTRAFILE} ${DBNAME} < ${sql};
  echo "Removing partitions";
  time mysql --defaults-extra-file=${EXTRAFILE} ${DBNAME} -e "ALTER TABLE \`history\` REMOVE PARTITIONING; ALTER TABLE \`history_log\` REMOVE PARTITIONING; ALTER TABLE \`history_str\` REMOVE PARTITIONING; ALTER TABLE \`history_text\` REMOVE PARTITIONING; ALTER TABLE \`history_uint\` REMOVE PARTITIONING; ALTER TABLE \`trends\` REMOVE PARTITIONING; ALTER TABLE \`trends_uint\` REMOVE PARTITIONING;"
  rm -f ${sql};
fi
echo "Finished..";
cd $OLDPWD;
date;
