
from . import setup_yoda, destroy_yoda, set_etcd_key, MockHttpServer, \
    ETCD_PROXY_BASE, HTTP_TEST_TIMEOUT, _add_node, _add_location,\
    _request_proxy, CleanupEtcdFolders, _remove_node, _add_acl
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


def test_proxy_backend():
    with CleanupEtcdFolders(
            ['/upstreams/test-proxy-backend',
             '/hosts/test-proxy-backend.abc.com']):
        with MockHttpServer() as node1:
            with MockHttpServer() as node2:
                _add_node('test-proxy-backend', 'node1', node1)
                _add_node('test-proxy-backend', 'node2', node2)
                _add_location('test-proxy-backend.abc.com',
                              'test-proxy-backend')
                #Wait 5s for changes to apply
                sleep(5)
                for protocol in ['http', 'https']:
                    resp = _request_proxy('test-proxy-backend.abc.com',
                                          protocol=protocol)
                    assert_equals(resp.status_code, 200)


def test_proxy_with_force_ssl():
    with CleanupEtcdFolders(
            ['/upstreams/test-proxy-force-ssl',
             '/hosts/test-proxy-force-ssl.abc.com']):
        with MockHttpServer() as node1:
            _add_node('test-proxy-force-ssl', 'node1', node1)
            _add_location('test-proxy-force-ssl.abc.com',
                          'test-proxy-force-ssl', force_ssl=True)
            #Wait 5s for changes to apply
            sleep(5)

            resp = _request_proxy('test-proxy-force-ssl.abc.com')
            assert_equals(resp.status_code, 301)
            assert_equals(resp.headers['location'],
                          'https://test-proxy-force-ssl.abc.com/')


def test_proxy_when_all_upstream_nodes_gets_removed():
    with CleanupEtcdFolders(
            ['/upstreams/test-nodes-removal',
             '/hosts/test-nodes-removal.abc.com']):
        with MockHttpServer() as node1:

            #Given: Proxy with existing nodes
            #First we add nodes
            _add_node('test-nodes-removal', 'node1', node1)
            _add_location('test-nodes-removal.abc.com',
                          'test-nodes-removal')

            #Wait 5s for changes to apply
            sleep(5)

            #Validate that proxy was setup
            resp = _request_proxy('test-nodes-removal.abc.com')
            assert_equals(resp.status_code, 200)

            #When: I remove the backend nodes
            _remove_node('test-nodes-removal', 'node1', node1)
            #Wait 5s for changes to apply
            sleep(5)

            #Validate that No BE node is available for servicing request
            resp = _request_proxy('test-nodes-removal.abc.com')
            assert_equals(resp.status_code, 503)


def test_proxy_with_denied_acls():
    with CleanupEtcdFolders(
            ['/upstreams/test-denied-acl', '/global/acls/test-denied-acl',
             '/hosts/test-denied-acl.abc.com']):
        with MockHttpServer() as node1:
            _add_node('test-denied-acl', 'node1', node1)
            _add_acl('test-denied-acl', '0.0.0.0/0')
            _add_location('test-denied-acl.abc.com', 'test-denied-acl',
                          denied_acls={'d1': 'test-denied-acl'})
            #Wait 5s for changes to apply
            sleep(5)

            resp = _request_proxy('test-denied-acl.abc.com')
            assert_equals(resp.status_code, 403)


def test_proxy_with_allowed_acls():
    with CleanupEtcdFolders(
            ['/upstreams/test-allowed-acl', '/global/acls/test-allowed-acl',
             '/hosts/test-allowed-acl.abc.com']):
        with MockHttpServer() as node1:
            _add_node('test-allowed-acl', 'node1', node1)
            _add_acl('test-allowed-acl', '255.255.255.255/32')
            _add_location('test-allowed-acl.abc.com', 'test-allowed-acl',
                          allowed_acls={'a1': 'test-allowed-acl'})
            #Wait 5s for changes to apply
            sleep(5)

            resp = _request_proxy('test-allowed-acl.abc.com')
            assert_equals(resp.status_code, 403)