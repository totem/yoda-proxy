__author__ = 'sukrit'

import os
import time
from subprocess import call, check_call
import SimpleHTTPServer
import SocketServer
import etcd

from threading import Thread

DOCKER = os.environ.get('DOCKER_CMD', 'docker -H 127.0.0.1:8283')
ETCD_PROXY_BASE = os.environ.get('ETCD_PROXY_BASE', '/yoda-integration')
ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
ETCD_PORT = int(os.environ.get('ETCD_POR', '4001'))
HTTP_TEST_TIMEOUT=10  #In seconds
MODULE_DIR=os.path.abspath(os.path.dirname(__file__))


def build_yoda():
    check_call(
        '{DOCKER} build --rm  -t totem/yoda-integration {MODULE_DIR}/../../'
        .format(DOCKER=DOCKER, MODULE_DIR=MODULE_DIR), shell=True)


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
    delete_etcd_dir()
    pass


def get_etcd_client():
    return etcd.Client(host=ETCD_HOST, port=ETCD_PORT)

def set_etcd_key(key, value):
    use_key = '%s%s' % (ETCD_PROXY_BASE,key)
    get_etcd_client().set(use_key, value)


def delete_etcd_dir(key=None):
    use_key = '%s%s' % (ETCD_PROXY_BASE,key) if key else ETCD_PROXY_BASE
    get_etcd_client().delete(use_key,recursive=True, dir=True)

