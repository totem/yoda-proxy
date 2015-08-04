FROM totem/totem-base:trusty-1.0.2
ENV DEBIAN_FRONTEND noninteractive
ENV ETCDCTL_VERSION v0.4.6

RUN apt-get update && \
    apt-get install -y haproxy/trusty-backports nano && \
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

#AWS Cli and Supervisor
RUN pip install awscli==1.4.1 supervisor==3.1.2 supervisor-stdout

#Haproxy
RUN mkdir -p /run/haproxy && chown -R haproxy:haproxy /run/haproxy
ADD ./bin/haproxy-wrapper.sh /usr/sbin/haproxy-wrapper.sh
RUN chmod 550 /usr/sbin/haproxy-wrapper.sh

#Etcdctl
RUN curl -L https://github.com/coreos/etcd/releases/download/$ETCDCTL_VERSION/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz -o /tmp/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz && \
    cd /tmp && gzip -dc etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz | tar -xof - && \
    cp -f /tmp/etcd-$ETCDCTL_VERSION-linux-amd64/etcdctl /usr/local/bin && \
    rm -rf /tmp/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz

#Supervisor
#Supervisor Config
RUN mkdir -p /var/log/supervisor && \
    mkdir -p /etc/supervisor/conf.d
ADD etc/supervisor/conf.d/supervisord.conf /etc/supervisor/conf.d/
ADD etc/supervisor/supervisord.conf /etc/supervisor/
RUN ln -sf /etc/supervisor/supervisord.conf /etc/supervisord.conf
ADD bin/supervisord-wrapper.sh /usr/sbin/supervisord-wrapper.sh
RUN chmod +x /usr/sbin/supervisord-wrapper.sh && \
    ln -sf /etc/supervisor/supervisord.conf /etc/supervisord.conf

#Confd
ENV CONFD_VERSION 0.7.1
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v$CONFD_VERSION/confd-${CONFD_VERSION}-linux-amd64 -o /usr/local/bin/confd && \
    chmod 555 /usr/local/bin/confd

#Confd Defaults
ADD ./bin/confd-wrapper.sh /usr/sbin/confd-wrapper.sh
RUN chmod 550 /usr/sbin/confd-wrapper.sh
ADD etc/confd /etc/confd

#Certificates Sync Job
ADD ./bin/sync-certs.sh /usr/sbin/sync-certs.sh
RUN chmod 550 /usr/sbin/sync-certs.sh

#Default Certs
ADD /etc/haproxy/certs.d /etc/haproxy/certs.d

EXPOSE 80 443 8081

ENTRYPOINT ["/usr/sbin/supervisord-wrapper.sh"]
