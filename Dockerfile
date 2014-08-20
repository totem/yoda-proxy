FROM totem/totem-base:trusty
ENV DEBIAN_FRONTEND noninteractive
ENV ETCDCTL_VERSION v0.4.6

RUN apt-get update
RUN apt-get install -y haproxy/trusty-backports supervisor openssh-server nano

#AWS Cli
RUN pip install awscli==1.4.1

#Syslog
RUN echo '$PreserveFQDN on' | cat - /etc/rsyslog.conf > /tmp/rsyslog.conf && sudo mv /tmp/rsyslog.conf /etc/rsyslog.conf
RUN sed -i 's~^#\$ModLoad immark\(.*\)$~$ModLoad immark \1~' /etc/rsyslog.conf

#Haproxy
RUN mkdir -p /run/haproxy && chown -R haproxy:haproxy /run/haproxy
ADD ./bin/haproxy-wrapper.sh /usr/sbin/haproxy-wrapper.sh
RUN chmod 550 /usr/sbin/haproxy-wrapper.sh

#Etcdctl
RUN curl -L https://github.com/coreos/etcd/releases/download/$ETCDCTL_VERSION/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz -o /tmp/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz
RUN cd /tmp && gzip -dc etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz | tar -xof -
RUN cp -f /tmp/etcd-$ETCDCTL_VERSION-linux-amd64/etcdctl /usr/local/bin
RUN rm -rf /tmp/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz

##SSH Server (To troubleshoot issues with image factory)
RUN mkdir /var/run/sshd
ADD root/.ssh /root/.ssh
RUN chmod -R 400 /root/.ssh/* && chmod  500 /root/.ssh & chown -R root:root /root/.ssh

#Supervisor
ADD etc/supervisor /etc/supervisor

#Confd
ENV CONFD_VERSION 0.6.0-alpha3
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v$CONFD_VERSION/confd-${CONFD_VERSION}-linux-amd64 -o /usr/local/bin/confd
RUN chmod 555 /usr/local/bin/confd

#Confd Defaults
ADD ./bin/confd-wrapper.sh /usr/sbin/confd-wrapper.sh
RUN chmod 550 /usr/sbin/confd-wrapper.sh
ADD etc/confd /etc/confd

#Certificates Sync Job
ADD ./bin/sync-certs.sh /usr/sbin/sync-certs.sh
RUN chmod 550 /usr/sbin/sync-certs.sh

#Default Certs
ADD /etc/haproxy/certs.d /etc/haproxy/certs.d

#Env variables that can be overridden
ENV ETCD_URL 172.17.42.1:4001
ENV ETCD_PROXY_BASE /yoda
ENV PROXY_HOST yoda.local.sh
ENV SYNC_CERTS false
ENV S3_YODA_BUCKET yoda-mubucket

EXPOSE 22 80 443 8081

ENTRYPOINT ["/usr/bin/supervisord"]
CMD ["-n"]
