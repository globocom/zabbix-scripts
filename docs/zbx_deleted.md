# zbx_deleted.py
Remove hosts that have been too long on hostgroup called \_DELETED\_ and hosts that have no timestamp.

# Usage:
```sh
usage: zbx_deleted.py [-h] --url URL --user USER --password PASSWORD
                      [--no-verbose] [--verbose] [--loglevel LOGLEVEL]
                      [--max-age MAX_AGE] [--no-run] [--run] [--no-matches]
                      [--matches]

Script used to remove hosts older than --max-age days from hostgroup _DELETED_
(hostgroupid=72)

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Dont show any logs on screen
  --verbose
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
  --max-age MAX_AGE    Max age in days for host to be in there
  --no-run             Dont remove any host, just count
  --run                Remove all hosts that expired
  --no-matches         Dont remove any host that has no prefix
  --matches            Remove all hosts that has no prefix
```

# TODO
> - Use hostgroupname instead of hostgroupid
