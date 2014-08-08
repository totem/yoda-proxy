FROM totem/totem-base:trusty
ENV DEBIAN_FRONTEND noninteractive
ENV ETCDCTL_VERSION v0.4.6

RUN apt-get update
RUN apt-get install -y haproxy/trusty-backports supervisor openssh-server

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
ENV CONFD_VERSION 0.3.0
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v$CONFD_VERSION/confd_${CONFD_VERSION}_linux_amd64.tar.gz -o /tmp/confd_${CONFD_VERSION}_linux_amd64.tar.gz
RUN cd /tmp && tar -zxvf confd_${CONFD_VERSION}_linux_amd64.tar.gz
RUN mv /tmp/confd /usr/local/bin
RUN rm -rf /tmp/confd_${CONFD_VERSION}_linux_amd64.tar.gz

#Confd Defaults
RUN mkdir -p /etc/confd/{conf.d,templates}
ADD ./bin/confd-wrapper.sh /usr/sbin/confd-wrapper.sh
RUN chmod 550 /usr/sbin/confd-wrapper.sh
ADD etc/confd /etc/confd


#Env variables that can be overridden
ENV ETCD_URL 172.17.0.1:4001
ENV ETCD_PROXY_BASE /yoda

EXPOSE 22 80 8081

ENTRYPOINT ["/usr/bin/supervisord"]
