#!/bin/bash -le

sed -i s/127.0.0.1[:]4001/$ETCD_URL/g /etc/confd/confd.toml
confd