# zbx_changeMultipleTriggers.py
Change status of multiple triggers inside multiple hosts

# Usage:
```sh
usage: zbx_changeMultipleTriggers.py [-h] [--url URL] [--user USER]
                                     [--password PASSWORD] [--no-verbose]
                                     [--verbose] [--no-run] [--run] --status
                                     STATUS [--loglevel LOGLEVEL]

Change status of multiple triggers in multiple Zabbix Hosts.

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Dont show any logs on screen
  --verbose
  --no-run             Work
  --run                Dont perform any operation
  --status STATUS      Status to change trigger to. [0|1]
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
```

# TODO
> - Hosts and triggers should be in a separate file
