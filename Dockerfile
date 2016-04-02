FROM python:2.7-slim
ENV DEBIAN_FRONTEND noninteractive
ENV ETCDCTL_VERSION v0.4.6
ENV CONFD_VERSION 0.7.1

# Native packages, python depdencies, aws cli, supervisor, dumb-init, etcd
RUN apt-get update && \
    # Haproxy
    apt-get install -y haproxy curl wget && \
    mkdir -p /run/haproxy && \
    chown -R haproxy:haproxy /run/haproxy && \

    # Confd
    curl -L https://github.com/kelseyhightower/confd/releases/download/v$CONFD_VERSION/confd-${CONFD_VERSION}-linux-amd64 -o /usr/local/bin/confd && \
    chmod 555 /usr/local/bin/confd && \

    # AWS Cli, Supervisor
    pip install awscli==1.4.1 supervisor==3.1.2 supervisor-stdout && \

    # Dumb Init
    wget -O /usr/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.0.0/dumb-init_1.0.0_amd64 && \
    chmod +x /usr/bin/dumb-init && \

    # Etcd
    curl -L https://github.com/coreos/etcd/releases/download/$ETCDCTL_VERSION/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz -o /tmp/etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz && \
    cd /tmp && gzip -dc etcd-$ETCDCTL_VERSION-linux-amd64.tar.gz | tar -xof - && \
    cp -f /tmp/etcd-$ETCDCTL_VERSION-linux-amd64/etcdctl /usr/local/bin && \

    # Cleanup
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/* /tmp/*

# Configs , Custom Scripts

#Supervisor Config
RUN mkdir -p /var/log/supervisor && \
    mkdir -p /etc/supervisor/conf.d && \
    ln -sf /etc/supervisor/supervisord.conf /etc/supervisord.conf
ADD etc/supervisor/conf.d/supervisord.conf /etc/supervisor/conf.d/
ADD etc/supervisor/supervisord.conf /etc/supervisor/

# Confd Config
ADD etc/confd /etc/confd

#Certificates Sync Job
ADD ./bin/sync-certs.sh /usr/sbin/sync-certs.sh
RUN chmod 550 /usr/sbin/sync-certs.sh

#Default Certs
ADD /etc/haproxy/certs.d /etc/haproxy/certs.d

#Custom Scripts
ADD ./bin/*.sh /usr/sbin/
RUN chmod -R +x /usr/sbin


EXPOSE 80 443 8081

ENTRYPOINT ["/usr/bin/dumb-init", "/usr/sbin/supervisord-wrapper.sh"]