#!/bin/bash -el
CERTS_FOLDER=/etc/haproxy/certs.d
mkdir -p $CERTS_FOLDER
if [ "$SYNC_CERTS" == "true" ]; then
  while [ 1 ]
  do

      aws s3 sync --delete s3://$S3_YODA_BUCKET/certs.d $CERTS_FOLDER
      #This is not perfect, but certs are typically not added that frequently
      if [ "$(find $CERTS_FOLDER -type f -mmin -6  | wc -l)" -gt 0 ]; then
         echo "Change detected. Reloading haproxy..."
         #This call may leak a process if its reload, and confd reload is in progress
         #May be we can use confd reload mechanism in future.
         /etc/init.d/haproxy reload
      fi
      #Make sure to update --mmin flag if the sleep time changes.
      sleep 300s

  done

else
  echo "Skipping SYNC_CERTS. In order to enable this feature set environment variable SYNC_CERTS to true"
  #Sleep forever
  sleep infinity
fi
