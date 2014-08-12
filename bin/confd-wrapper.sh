#!/bin/bash -le

ETCDCTL="etcdctl --peers $ETCD_URL"
#Create initial directories if the do not exist
for directory in global locations backends
do
  $ETCDCTL ls $ETCD_PROXY_BASE/$directory || $ETCDCTL mkdir $ETCD_PROXY_BASE/$directory
done

#Create Default Keys (For port bindings)
LISTENER_PATH=$ETCD_PROXY_BASE/global/listener
$ETCDCTL get $LISTENER_PATH/http/bind  || $ETCDCTL set $LISTENER_PATH/http/bind *:80
$ETCDCTL get $LISTENER_PATH/https/bind || $ETCDCTL set $LISTENER_PATH/https/bind *:443
$ETCDCTL get $LISTENER_PATH/admin/bind || $ETCDCTL set $LISTENER_PATH/admin/bind *:8081


sed -i -e "s/127.0.0.1[:]4001/$ETCD_URL/g" /etc/confd/confd.toml
sed -i -e "s|/yoda|$ETCD_PROXY_BASE|g" /etc/confd/conf.d/haproxy.toml
confd