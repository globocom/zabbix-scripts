#!/bin/bash
# Copyright (c) 2019, Globo.com <https://github.com/globocom>
# This file is part of globocom/zabbix-scripts
# (see https://github.com/globocom/zabbix-scripts).
# License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause

prep_arq()
{
    file="/tmp/dsn.txt"
    user_conn="usr_zabbix"

    cp /etc/odbc.ini $file

    sed -i '/^\[/!d' $file

    sed -i 's/\]//' $file
    sed -i 's/\[//' $file
}


test_conn()
{
    prep_arq

    for dsn in $(cat $file);
        do
            echo "Testing connection using DSN $dsn"

            /usr/bin/isql $dsn $user_conn < /tmp/quit.sql

            if [ "$?" -ne 0 ]; then
                echo "Connection failed!!!"
                echo $dsn >> /tmp/error_conn_odbc.txt
            else
                echo "Success in connection!!!"
            fi

            echo
            sleep 5
        done
}

which isql > /dev/null
if [ "$?" -ne 0 ]; then
    echo "isql binary not found."
    exit
else
    test_conn
fi