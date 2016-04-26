#!/bin/bash -el
CERTS_FOLDER=/etc/haproxy/certs.d
mkdir -p $CERTS_FOLDER

function sync_certs {
  aws s3 sync --delete s3://$S3_YODA_BUCKET/certs.d $CERTS_FOLDER
      #This is not perfect, but certs are typically not added that frequently
      if [ "$1" == "true" ] || [ "$(find $CERTS_FOLDER -type f -mmin -6  | wc -l)" -gt 0 ];  then
         echo "Change detected (force: $1). Reloading haproxy..."
         /usr/sbin/haproxy-reload.sh
      fi
}

if [ "$SYNC_CERTS" == "true" ]; then
  sync_certs true # Force sync for first run
  while [ 1 ]
  do
      #Make sure to update --mmin flag if the sleep time changes.
      sleep 300s
      sync_certs false
  done

else
  echo "Skipping SYNC_CERTS. In order to enable this feature set environment variable SYNC_CERTS to true"
  #Sleep forever
  sleep infinity
fi
