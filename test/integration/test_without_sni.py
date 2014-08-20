
from . import setup_yoda, destroy_yoda, set_etcd_key, MockHttpServer, \
    ETCD_PROXY_BASE, HTTP_TEST_TIMEOUT
from nose.tools import assert_equals

import requests

from time import sleep

from urllib2 import urlopen, HTTPError


__author__ = 'sukrit'


def setup_module():
    setup_yoda()
    pass


def teardown_module():
    destroy_yoda()
    pass


def test_http_port_bindings():
    resp = requests.get('http://127.0.0.1:80', timeout=HTTP_TEST_TIMEOUT)
    #No Service available
    assert_equals(resp.status_code, 503)


def test_https_port_bindings():
    resp = requests.get('https://127.0.0.1:443', timeout=HTTP_TEST_TIMEOUT,
                        verify=False)
    #No Service available
    assert_equals(resp.status_code, 503)

def _add_node(upstream, node_name, endpoint):
    set_etcd_key('/upstreams/{upstream}/endpoints/{node_name}'.format(
        upstream=upstream, node_name=node_name
    ), endpoint)


def _add_location(host, upstream, location_name='home', path='/',
                  allowed_acls={'a1':'public'}, denied_acls={},
                  force_ssl=False):
    location_key='/hosts/{host}/locations/{location_name}'.format(
        host=host, location_name=location_name)

    for acl_key,acl_value in allowed_acls:
         set_etcd_key('{location_key}/allowed/{acl_key}'.format(
             location_key=location_key, acl_key=acl_key
         ), acl_value)

    for acl_key,acl_value in denied_acls:
        set_etcd_key('{location_key}/denied/{acl_key}'.format(
            location_key=location_key, acl_key=acl_key
        ), acl_value)

    set_etcd_key('{location_key}/path'.format(location_key=location_key), path)
    set_etcd_key('{location_key}/force-ssl'.format(location_key=location_key),
                 force_ssl)
    set_etcd_key('{location_key}/upstream'.format(location_key=location_key),
                 upstream)


def test_proxy_backend():
    with MockHttpServer() as node1:
        with MockHttpServer() as node2:
            _add_node('myapp.abc.com-v1', 'node1', node1)
            _add_node('myapp.abc.com-v1', 'node2', node2)
            _add_location('myapp.abc.com', 'myapp.abc.com-v1')
            #Wait 5s for changes to apply
            sleep(5)
            resp = requests.get(
                'http://localhost',
                timeout=HTTP_TEST_TIMEOUT,
                headers = {
                 'Host': 'myapp.abc.com'
                },
                verify=False)
            assert_equals(resp.status_code, 200)