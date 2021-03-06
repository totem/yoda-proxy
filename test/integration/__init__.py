__author__ = 'sukrit'

import os
import SimpleHTTPServer
import SocketServer
import etcd
import requests

from threading import Thread

ETCD_PROXY_BASE = os.environ.get('ETCD_PROXY_BASE', '/yoda')
ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
ETCD_PORT = int(os.environ.get('ETCD_PORT', '4001'))
MOCK_TCP_PORT = int(os.environ.get('MOCK_TCP_PORT', '31325'))
HOST_IP = os.environ.get('HOST_IP', '127.0.0.1')
YODA_HOST = os.environ.get('YODA_HOST', HOST_IP)
HTTP_TEST_TIMEOUT = 6  # In seconds
MODULE_DIR = os.path.abspath(os.path.dirname(__file__))


class MockHttpServer:

    def __init__(self, host=None, port=None, handler=None):
        self.port = port or 0
        self.httpd = SocketServer.TCPServer(
            (host or HOST_IP, self.port),
            handler or SimpleHTTPServer.SimpleHTTPRequestHandler)

    def __enter__(self):
        thread = Thread(target=self.httpd.serve_forever)
        thread.daemon = True
        thread.start()
        return '{}:{}'.format(self.httpd.server_address[0],
                              self.httpd.server_address[1])

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.httpd.shutdown()


class XFrameOptionsHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def end_headers(self):
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)


class CleanupEtcdFolders:
    def __init__(self, keys):
        self.keys = keys or []

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self.keys:
            delete_etcd_dir(key)


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
                  force_ssl=False, aliases={}):
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
                 'true' if force_ssl else 'false')
    set_etcd_key('{location_key}/upstream'.format(location_key=location_key),
                 upstream)
    for name, alias in aliases.iteritems():
        set_etcd_key('/hosts/{host}/aliases/{name}'.format(
            host=host, name=name), alias)


def _request_proxy(host, protocol='http', allow_redirects=False, port=None,
                   path='/'):
    port = port or {
        'http': 80,
        'https': 443,
    }[protocol]
    return requests.get(
        '%s://%s:%d%s' % (protocol, YODA_HOST, port, path),
        timeout=HTTP_TEST_TIMEOUT,
        headers={
            'Host': host
        },
        verify=False, allow_redirects=allow_redirects)
