#!/bin/sh
# 2015.08.26 - @fpaternot
# 
# Based on
# http://stackoverflow.com/questions/67093/how-do-i-quickly-rename-a-mysql-database-change-schema-name

user='root'
date;
db="$1";
if [ "x$db" == "x" ]; then
  echo "rename-database.sh DATABASE";
  exit 1;
fi
newdb="${db}_`date +%Y%m%d_%H%M`";

echo "Renaming from ${db} to ${newdb}";
echo ""

echo "Clear history and trends tables of ${db}";
mysql -u${user} $db -e "TRUNCATE history; TRUNCATE history_log; TRUNCATE history_str; TRUNCATE history_text; TRUNCATE history_uint; TRUNCATE trends; TRUNCATE trends_uint;";

echo "Import old db into new database";
mysql -u${user} -e "CREATE DATABASE ${newdb};";
time mysqldump -u${user} --opt --single-transaction --skip-lock-tables --extended-insert=FALSE ${db} | mysql -u${user} -D ${newdb} > /dev/null;

echo "Remove old database: ${db}";
mysql -u${user} -e "DROP DATABASE ${db};";


echo 'Finished';
date;
