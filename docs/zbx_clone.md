# zbx_clone.py


# Usage:
```sh
usage: zbx_clone.py [-h] [--url URL] [--user USER] [--password PASSWORD]
                    [--no-verbose] [--verbose] [--loglevel LOGLEVEL] [--hosts]
                    [--no-hosts] [--proxy] [--no-proxy] [--proxy-local]
                    [--no-proxy-local] [--discovery] [--no-discovery] [--mail]
                    [--no-mail]

Changes all passive proxies to active

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Don't show any logs on screen
  --verbose
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
  --hosts              Disable all hosts inside zabbix
  --no-hosts           Keep the state as is, from all hosts
  --proxy              Change all proxies to active
  --no-proxy           Dont change proxy mode
  --proxy-local        Change all passive proxies to localhost
  --no-proxy-local     Dont change passive proxies address
  --discovery          Disable all network discovery rules
  --no-discovery       Keep state of all network discovery rules
  --mail               Change email source address to zabbix-
                       AMBIENTE@suaempresa.com
  --no-mail            Keep current email source address
```

# TODO
> - Hosts and triggers should be in a separate file
