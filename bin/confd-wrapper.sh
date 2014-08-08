#!/bin/bash -le

sed -i -e "s/127.0.0.1[:]4001/$ETCD_URL/g" -e "s|/yoda|$ETCD_PROXY_BASE|g" /etc/confd/confd.toml
confd