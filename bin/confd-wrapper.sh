#!/bin/bash -le

ETCDCTL="etcdctl --peers $ETCD_URL"
#Create initial directories if the do not exist
for directory in global hosts upstreams
do
  $ETCDCTL ls $ETCD_PROXY_BASE/$directory || $ETCDCTL mkdir $ETCD_PROXY_BASE/$directory
done

#Yoda proxy init parameters
$ETCDCTL get $ETCD_PROXY_BASE/global/hostname  || $ETCDCTL set $ETCD_PROXY_BASE/global/hostname $PROXY_HOST
$ETCDCTL get $ETCD_PROXY_BASE/global/control/reload || $ETCDCTL  set $ETCD_PROXY_BASE/global/control/reload $(($(date +'%s * 1000 + %-N / 1000000')))

#Create Default Keys (For port bindings)
LISTENER_PATH=$ETCD_PROXY_BASE/global/listeners
$ETCDCTL get $LISTENER_PATH/http/bind  || $ETCDCTL set $LISTENER_PATH/http/bind 0.0.0.0:80
$ETCDCTL get $LISTENER_PATH/https/bind || $ETCDCTL set $LISTENER_PATH/https/bind 0.0.0.0:443
$ETCDCTL get $LISTENER_PATH/admin/bind || $ETCDCTL set $LISTENER_PATH/admin/bind localhost:8081

#Default ACLs
$ETCDCTL get $ETCD_PROXY_BASE/global/acls/public/cidr/src || $ETCDCTL set $ETCD_PROXY_BASE/global/acls/public/cidr/src "0.0.0.0/0"
$ETCDCTL get $ETCD_PROXY_BASE/global/acls/global-black-list/cidr/src || $ETCDCTL set $ETCD_PROXY_BASE/global/acls/global-black-list/cidr/src ""

sed -i -e "s/172.17.42.1[:]4001/$ETCD_URL/g" -e "s|/yoda|$ETCD_PROXY_BASE|" /etc/confd/confd.toml
#sed -i -e "s|/yoda|$ETCD_PROXY_BASE|g" /etc/confd/conf.d/haproxy.toml
confd