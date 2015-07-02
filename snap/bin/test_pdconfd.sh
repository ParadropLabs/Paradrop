#!/bin/bash

config_file=/home/ubuntu/config

if [ -e $config_file ]; then
    echo "Configuration file $config_file exists, not overwriting."
else
    echo "Generating configuration file ${config_file}..."

    cat >$config_file <<EOF
config interface lan
    option proto 'static'
    option ipaddr '192.168.32.1'
    option netmask '255.255.255.0'
    option ifname 'eth1'

config dhcp lan
    option interface 'lan'
    option start '100'
    option limit '150'
    option leasetime '12h'
EOF
fi

echo "Poking pdconfd..."
dbus-send --system --print-reply --dest=com.paradrop.config / com.paradrop.config.Reload string:$config_file
