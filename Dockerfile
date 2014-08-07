FROM totem/totem-base:trusty
RUN apt-get update

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get install -y haproxy/trusty-backports supervisor

ADD bin/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
