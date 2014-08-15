#!/bin/bash -le
PID_FILE="/var/run/haproxy.pid"

/etc/init.d/haproxy restart

#Trap SIGINT or SIGTERM and stop haproxy
trap "/etc/init.d/haproxy stop; exit" SIGINT SIGTERM

#Check if there exists at-least 1 process running as haproxy user.
while ps -u haproxy 1>/dev/null ;
do
  #Possible report process to etcd with ttl.
  sleep 20s
done

echo "Haproxy Process heartbeat did not succeed. Exitting wrapper..."