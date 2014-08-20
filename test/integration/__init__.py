__author__ = 'sukrit'

import os
import time
import requests
from subprocess import call, check_call
import SimpleHTTPServer
import SocketServer
from threading import Thread

DOCKER = os.environ.get('DOCKER_CMD', 'docker -H 127.0.0.1:8283')
ETCD_PROXY_BASE = os.environ.get('ETCD_PROXY_BASE', '/yoda-integration')
ETCDCTL = os.environ.get('ETCDCTL_CMD', 'etcdctl')
HTTP_TEST_TIMEOUT=10  #In seconds


def build_yoda():
    check_call(
        '%s build --rm  -t totem/yoda-integration ../../' % DOCKER, shell=True)


def setup_yoda_sni():
    build_yoda()


def setup_yoda():
    build_yoda()
    check_call(
        '{DOCKER} run --name yoda-integration -d -P -p 80:80 -p 443:443 '
        '-e ETCD_PROXY_BASE={ETCD_PROXY_BASE} -h yoda-integration-{USER} '
        'totem/yoda-integration'
        .format(DOCKER=DOCKER, ETCD_PROXY_BASE=ETCD_PROXY_BASE,
                USER=os.environ['USER']), shell=True)
    time.sleep(10)


class MockHttpServer:

    def __init__(self, host=None, port=None, handler=None):
        self.port = port or 0
        self.httpd = SocketServer.TCPServer(
            (host or "172.17.42.1", self.port),
            handler or SimpleHTTPServer.SimpleHTTPRequestHandler)

    def __enter__(self):
        thread = Thread(target=self.httpd.serve_forever)
        thread.daemon=True
        thread.start()
        return '{}:{}'.format(self.httpd.server_address[0],
                              self.httpd.server_address[1])

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.httpd.shutdown()


def destroy_yoda():
    call('%s stop yoda-integration' % DOCKER, shell=True)
    call('%s rm yoda-integration' % DOCKER, shell=True)
    call('%s rmi  totem/yoda-integration' % DOCKER, shell=True)
    call('{ETCDCTL} rm --recursive {ETCD_PROXY_BASE}'.format(
        ETCDCTL=ETCDCTL, ETCD_PROXY_BASE=ETCD_PROXY_BASE), shell=True)
    pass


def set_etcd_key(key, value):
    call('{ETCDCTL} set {ETCD_PROXY_BASE}{key} {value}'.format(
        ETCDCTL=ETCDCTL, ETCD_PROXY_BASE=ETCD_PROXY_BASE, key=key,value=value),
        shell=True)

