# **Zabbix-Scripts::DB**
---
This path contains database related scripts.

All scripts assumes you are running on your database server and have 'root' access. Changes may be required for your environment.

## backup.sh
---
> This script creates a database backup from Zabbix 2.4 configuration only.
> 
> It's very light (~1min for 500G database) because it does not backup data tables (history* and trends*), only their structures.
> 
>### Credits
>> Author: Ricardo Santos (rsantos at gmail.com)
>> 
>> http://zabbixzone.com/zabbix/backuping-only-the-zabbix-configuration/
>
>### Usage
> ```shell
> $ sh backup.sh your.database.address databasename
> ```

## restore.sh
---
> Based on the backup.sh, this one restores the database.
> 
>> Looks on the backupdir and selects the newest backup avaiable
>> Creates database
>> Restore backup
>> Remove *any* partition it may have
> 
> ### Credits
>> Author: Filipe Paternot (fpaternot at corp.globo.com)
> 
> ### Usage
> ```shell
> $ sh restore.sh database_name
> ```
>

## rename.sh
---
> Similar to restore, this one is mostly used to keep multiple copies of same database. 
> 
> We use it mostly to keep live backup's from different development environmnents.
> 
> 
> ### Credits
>> Author: Filipe Paternot (fpaternot at corp.globo.com)
> 
> ### Usage
> ```shell
> $ rename.sh database_name
> ```


## move_items.py
---
> `Still under development.`
> 
> This one intends to revert data loss of specific items by making inserts to trends or trends_uint table (we ignore history, for now at least) based on a live backup database.
> 
> It assumes you for whatever reason lost something in currenct live database and has a backup to recover from, but cant simply overwrite all database and want to recover only some slice of data you missed.
> 
> ### Overall flow
> 1. Connects to Zabbix API to find hostid's
> 
> 1. Connects to current database and searches for:
>   1. Given a hostid, lists current items, filtering for desired key_ pattern
>
> 1. Connects to backup database and searches for:
>   1. Same hostid and the same key_'s
> 
> 1. With the match list of all itemid's:
>   1. Select all data from trends or trends_uint for each itemid
>   1. Creates bulk inserts, 1000 values each, and writes them to .sql file
>   1. Each file has up to 1M values (1k lines)
> 
>   1. Next step then is for you/your DBA to import this scripts to current database. Should be harmless, but if your DB is busy, better have someone watching the task.
>
> ### Usage
> ```shell
> $ python move_items.py --help
> $ python move_items.py --url=http://localhost --zuser=admin --zpass=zabbix --dbuser=zabbix --dbpassword='' --dbbkphost=BKPHOST --dblivehost=localhost --verbose --loglevel=INFO
> ```
> 
> ### TODO
> * Args to filter the item key_'s
> * Args to filter hostgroupid
>
