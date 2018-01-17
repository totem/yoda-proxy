#!/bin/bash -le

HOST_IP="${HOST_IP:-127.0.0.1}"

cat <<END>> /etc/profile.d/cluster-deployer-env.sh
export HOST_IP='${HOST_IP}'
export ETCD_URL='${ETCD_URL:-${HOST_IP}:4001}'
export ETCDCTL="${ETCDCTL:-etcdctl --peers $ETCD_URL}"
export ETCD_PROXY_BASE='${ETCD_PROXY_BASE:-/yoda}'
export PROXY_HOST='${PROXY_HOST:-yoda.local.sh}'
export SYNC_CERTS='${SYNC_CERTS:-false}'
export S3_YODA_BUCKET='${S3_YODA_BUCKET:-yoda-certs}'
export LOG_IDENTIFIER='${LOG_IDENTIFIER:-yoda-proxy}'
export GOMAXPROCS='${GOMAXPROCS:-1}'
export YODA_WATCH_INTERVAL='${YODA_WATCH_INTERVAL:-10}'
END

if [ ! -e /dev/log ]; then
  service rsyslog start
fi

$ETCDCTL cluster-health

/bin/bash -le -c "/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf"
