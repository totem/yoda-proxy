#!/bin/bash

HAPROXY_LOCK="${HAPROXY_LOCK:-/var/lock/haproxy-reload.lock}"
HAPROXY_RELOAD_TIMEOUT="${HAPROXY_RELOAD_TIMEOUT:-30s}"
HAPROXY_RELOAD_SLEEP="${HAPROXY_RELOAD_SLEEP:-1s}"

/usr/bin/flock -o  $HAPROXY_LOCK -c "/usr/bin/timeout 30s /etc/init.d/haproxy reload && sleep $HAPROXY_RELOAD_SLEEP"