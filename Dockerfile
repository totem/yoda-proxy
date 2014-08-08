FROM totem/totem-base:trusty
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y haproxy/trusty-backports supervisor openssh-server

#Haproxy
RUN mkdir -p /run/haproxy && chown -R haproxy:haproxy /run/haproxy
ADD ./bin/haproxy-wrapper.sh /usr/sbin/haproxy-wrapper.sh
RUN chmod 550 /usr/sbin/haproxy-wrapper.sh

##SSH Server (To troubleshoot issues with image factory)
RUN mkdir /var/run/sshd

ADD root/.ssh /root/.ssh
RUN chmod -R 400 /root/.ssh/* && chmod  500 /root/.ssh & chown -R root:root /root/.ssh

ADD etc/supervisor /etc/supervisor

EXPOSE 22 80

ENTRYPOINT ["/usr/bin/supervisord"]
