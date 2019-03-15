# **Zabbix-Scripts::ODBC**
---


## test_odbc_connection.sh
---
> Script to test connection for each DSN found in the odbc.ini configuration file
>
> For each connection error, your DSN will be included in the file /tmp/error_conn_odbc.txt
> 
>## Requisites
> * isql
> * ODBC drivers for your DBMS
> 
>### Credits
>> Author: Janssen Lima (janssen.lima at corp.globo.com)
>
>### Usage
> ```shell
> $ sh test_odbc_connection.sh
> ```
 
> ### TODO
> * Any suggestion? Pull request
>
