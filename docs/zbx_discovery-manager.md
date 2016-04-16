# zbx\_discovery-manager.py


# Usage:
```sh
usage: zbx_discovery-manager.py [-h] --url URL --user USER --password PASSWORD
                                [--no-verbose] [--verbose]
                                [--loglevel LOGLEVEL] [--fake FAKE]
                                [--no-move] [--move]

Create discovery rules for all necessary networks for Globo.com

optional arguments:
  -h, --help           show this help message and exit
  --url URL            Zabbix server address
  --user USER          Zabbix user
  --password PASSWORD  Zabbix password
  --no-verbose         Don't show any logs on screen
  --verbose
  --loglevel LOGLEVEL  Debug level. DEBUG/INFO/WARNING/ERROR/CRITICAL
  --fake FAKE          Just fake the execution and simulate the result (BETA)
  --no-move            Manage only new vlans. Existing ones will not be moved
                       between proxies (Better)
  --move
```