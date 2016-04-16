# zbx_deleteMonitors.py
Call Globo custom method deleteMonitors to remove a given hostname or, `evilly` remove all hosts from a given hostgroup. USE with **`CAUTION`**!

# Usage:
```sh
usage: zbx_deleteMonitors.py [-h] --url URL --user USER --password PASSWORD
                             [--no-verbose] [--verbose] [--loglevel LOGLEVEL]
                             [--hostname HOSTNAME] [--groupname GROUPNAME]
                             [--no-run] [--run]

This script removes all hosts from a given hostgroup id. It can also remove a
host by its name.

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Zabbix server address
  --user USER           Zabbix user
  --password PASSWORD   Zabbix password
  --no-verbose          Dont show any logs on screen
  --verbose
  --loglevel LOGLEVEL   Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
  --hostname HOSTNAME   Host name to be removed
  --groupname GROUPNAME
                        Hostgroup name to be cleaned (all hosts DELETED)! USE
                        WITH CAUTION
  --no-run              Dont remove anything, just count (works only with
                        hostgroup)
  --run                 Remove every match (works only with hostgroup)
```

# TODO
> - Nothing yet!
