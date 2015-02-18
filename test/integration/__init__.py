__author__ = 'sukrit'

import os
import time
from subprocess import call, check_call
import SimpleHTTPServer
import SocketServer
import etcd
import requests

from threading import Thread

DOCKER = os.environ.get('DOCKER_CMD', 'docker -H 127.0.0.1:8283')
ETCD_PROXY_BASE = os.environ.get('ETCD_PROXY_BASE', '/yoda-integration')
ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
ETCD_PORT = int(os.environ.get('ETCD_PORT', '4001'))
MOCK_TCP_PORT = int(os.environ.get('MOCK_TCP_PORT', '31325'))
HTTP_TEST_TIMEOUT = 10  # In seconds
MODULE_DIR = os.path.abspath(os.path.dirname(__file__))


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
        '-p {MOCK_TCP_PORT}:{MOCK_TCP_PORT} -e ETCD_PROXY_BASE'
        '={ETCD_PROXY_BASE} -h yoda-integration-{USER} totem/yoda-integration'
        .format(DOCKER=DOCKER, ETCD_PROXY_BASE=ETCD_PROXY_BASE,
                MOCK_TCP_PORT=MOCK_TCP_PORT, USER=os.environ['USER']),
        shell=True)
    time.sleep(10)


class MockHttpServer:

    def __init__(self, host=None, port=None, handler=None):
        self.port = port or 0
        self.httpd = SocketServer.TCPServer(
            (host or "172.17.42.1", self.port),
            handler or SimpleHTTPServer.SimpleHTTPRequestHandler)

    def __enter__(self):
        thread = Thread(target=self.httpd.serve_forever)
        thread.daemon = True
        thread.start()
        return '{}:{}'.format(self.httpd.server_address[0],
                              self.httpd.server_address[1])

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.httpd.shutdown()


class CleanupEtcdFolders:
    def __init__(self, keys):
        self.keys = keys or []

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self.keys:
            delete_etcd_dir(key)


def destroy_yoda():
    call('%s stop yoda-integration' % DOCKER, shell=True)
    call('%s rm yoda-integration' % DOCKER, shell=True)
    call('%s rmi  totem/yoda-integration' % DOCKER, shell=True)
    delete_etcd_dir()
    pass


def get_etcd_client():
    return etcd.Client(host=ETCD_HOST, port=ETCD_PORT)


def set_etcd_key(key, value):
    use_key = '%s%s' % (ETCD_PROXY_BASE, key)
    get_etcd_client().set(use_key, value)


def rm_etcd_key(key, value):
    use_key = '%s%s' % (ETCD_PROXY_BASE, key)
    get_etcd_client().delete(use_key, value)


def delete_etcd_dir(key=None, ignore_not_found=True):
    use_key = '%s%s' % (ETCD_PROXY_BASE, key) if key else ETCD_PROXY_BASE
    try:
        get_etcd_client().delete(use_key, recursive=True, dir=True)
    except KeyError:
        # Ignore if key is not found
        if not ignore_not_found:
            raise


def _add_node(upstream, node_name, endpoint):
    set_etcd_key('/upstreams/{upstream}/endpoints/{node_name}'.format(
        upstream=upstream, node_name=node_name
    ), endpoint)


def _add_upstream(upstream, mode='http', health_uri=None, health_timeout=None,
                  health_interval=None):
    set_etcd_key('/upstreams/{upstream}/mode'.format(upstream=upstream),
                 mode)
    if health_uri:
        set_etcd_key('/upstreams/{upstream}/health/uri'
                     .format(upstream=upstream), health_uri)
    if health_timeout:
        set_etcd_key('/upstreams/{upstream}/health/timeout'
                     .format(upstream=upstream), health_timeout)
    if health_interval:
        set_etcd_key('/upstreams/{upstream}/health/interval'
                     .format(upstream=upstream), health_interval)


def _add_tcp_listener(name, bind, upstream, allowed_acls={}, denied_acls={}):
    listener_key = '/global/listeners/tcp/%s' % name
    set_etcd_key('%s/bind' % listener_key, bind)
    set_etcd_key('%s/upstream' % listener_key, upstream)
    for acl_key, acl_value in allowed_acls.iteritems():
        set_etcd_key('%s/acls/allowed/%s' % (listener_key, acl_key),
                     acl_value)

    for acl_key, acl_value in denied_acls.iteritems():
        set_etcd_key('%s/acls/denied/%s' % (listener_key, acl_key),
                     acl_value)


def _add_acl(acl, cidr):
    set_etcd_key('/global/acls/{acl}/cidr/src'.format(acl=acl), cidr)


def _remove_node(upstream, node_name, endpoint):
    rm_etcd_key('/upstreams/{upstream}/endpoints/{node_name}'.format(
        upstream=upstream, node_name=node_name
    ), endpoint)


def _add_location(host, upstream, location_name='home', path='/',
                  allowed_acls={'a1': 'public'}, denied_acls={},
                  force_ssl=False):
    location_key = '/hosts/{host}/locations/{location_name}'.format(
        host=host, location_name=location_name)

    for acl_key, acl_value in allowed_acls.iteritems():
        set_etcd_key('{location_key}/acls/allowed/{acl_key}'.format(
            location_key=location_key, acl_key=acl_key
        ), acl_value)

    for acl_key, acl_value in denied_acls.iteritems():
        set_etcd_key('{location_key}/acls/denied/{acl_key}'.format(
            location_key=location_key, acl_key=acl_key
        ), acl_value)

    set_etcd_key('{location_key}/path'.format(location_key=location_key), path)
    set_etcd_key('{location_key}/force-ssl'.format(location_key=location_key),
                 force_ssl)
    set_etcd_key('{location_key}/upstream'.format(location_key=location_key),
                 upstream)


def _request_proxy(host, protocol='http', allow_redirects=False, port=None,
                   path='/'):
    port = port or {
        'http': 80,
        'https': 443,
    }[protocol]
    return requests.get(
        '%s://localhost:%d%s' % (protocol, port, path),
        timeout=HTTP_TEST_TIMEOUT,
        headers={
            'Host': host
        },
        verify=False, allow_redirects=allow_redirects)
