# zbx_historyGet.py
Collect data from whole hostgroups filtering by specific item inside all hosts.

Assumes all items have the same delta and data_type.

# Usage:
```sh
usage: zbx_historyGet.py [-h] --url URL --user USER --password PASSWORD
                         [--no-verbose] [--verbose] --group GROUP --item ITEM
                         [--loglevel LOGLEVEL]

Collect history data from selected items

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Dont show any logs on screen
  --verbose
  --group GROUP        Hostgroup name with hosts to look for
  --item ITEM          Item name inside each host of hostgroup
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
```

# TODO
> - Maybe allow multiple hostgroups and or item name
