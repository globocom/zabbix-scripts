# zbx_deleted-linux.py
Identify each Linux host inside \_DELETED\_ hostgroup that looks like a linux server, connect's and then disable service _SNMPD_. Also, disable the host in Zabbix.

This prevents network discovery from rediscovering the device and false-alarms.

# Usage:
```sh
usage: zbx_deleted-linux.py [-h] [--url URL] [--user USER]
                            [--password PASSWORD] [--no-verbose] [--verbose]
                            [--loglevel LOGLEVEL] [--sshkey SSHKEY]
                            [--groupid GROUPID]

This script connects to each server that looks like LINUX and stops its snmpd,
preventing removed hosts from beeing rediscovered.

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Dont show any logs on screen
  --verbose
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
  --sshkey SSHKEY      SSH Key to be used
  --groupid GROUPID    Groupid to be checked. Default: 72
```

# TODO
> - Some more testing
> - Improve output
