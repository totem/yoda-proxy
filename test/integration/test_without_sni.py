
from integration import \
    MockHttpServer, HTTP_TEST_TIMEOUT, _add_node, \
    _add_location, _request_proxy, CleanupEtcdFolders, _remove_node, \
    _add_acl, _add_upstream, _add_tcp_listener, MOCK_TCP_PORT, delete_etcd_dir, YODA_HOST
from nose.tools import assert_equals

import requests

from time import sleep

__author__ = 'sukrit'

PROXY_REFRESH_TIME = 5


def teardown_module():
    # delete_etcd_dir()
    pass


def test_http_port_bindings():
    resp = requests.get('http://{YODA_HOST}:80'.format(YODA_HOST=YODA_HOST),
                        timeout=HTTP_TEST_TIMEOUT)
    # Access denied (by default)
    assert_equals(resp.status_code, 403)


def test_https_port_bindings():
    resp = requests.get('http://{YODA_HOST}:80'.format(YODA_HOST=YODA_HOST),
                        timeout=HTTP_TEST_TIMEOUT, verify=False)
    # Access denied (by default)
    assert_equals(resp.status_code, 403)


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
                # Wait for sometime for changes to apply
                sleep(PROXY_REFRESH_TIME)
                for protocol in ['http', 'https']:
                    resp = _request_proxy('test-proxy-backend.abc.com',
                                          protocol=protocol)
                    assert_equals(resp.status_code, 200)


def test_backend_with_health_check():
    with CleanupEtcdFolders(
            ['/upstreams/test-health-check',
             '/hosts/test-health-check.abc.com']):
        with MockHttpServer() as node1:
            _add_upstream('test-health-check', health_uri='/',
                          health_timeout='2s', health_interval='1m')
            _add_node('test-health-check', 'node1', node1)
            _add_location('test-health-check.abc.com',
                          'test-health-check')
            # Wait for sometime for changes to apply
            sleep(PROXY_REFRESH_TIME)
            for protocol in ['http', 'https']:
                resp = _request_proxy('test-health-check.abc.com',
                                      protocol=protocol)
                assert_equals(resp.status_code, 200)


def test_tcp_proxy_backend():
    upstream = 'test-proxy-tcp-backend'
    with CleanupEtcdFolders(
            ['/upstreams/%s' % upstream,
             '/listeners/tcp/test-tcp']):
        with MockHttpServer() as node1:
            with MockHttpServer() as node2:
                _add_upstream(upstream, mode='tcp')
                _add_tcp_listener('test-tcp', '*:%d' % MOCK_TCP_PORT, upstream)
                _add_node(upstream, 'node1', node1)
                _add_node(upstream, 'node2', node2)
                # Wait 5s for changes to apply
                sleep(PROXY_REFRESH_TIME)
                for protocol in ['http']:
                    resp = _request_proxy('localhost', protocol=protocol,
                                          port=MOCK_TCP_PORT)
                    assert_equals(resp.status_code, 200)


def test_proxy_with_force_ssl():
    with CleanupEtcdFolders(
            ['/upstreams/test-proxy-force-ssl',
             '/hosts/test-proxy-force-ssl.abc.com']):
        with MockHttpServer() as node1:
            _add_node('test-proxy-force-ssl', 'node1', node1)
            _add_location('test-proxy-force-ssl.abc.com',
                          'test-proxy-force-ssl', force_ssl=True)
            # Wait for sometime for changes to apply
            sleep(PROXY_REFRESH_TIME)

            resp = _request_proxy('test-proxy-force-ssl.abc.com')
            assert_equals(resp.status_code, 301)
            assert_equals(resp.headers['location'],
                          'https://test-proxy-force-ssl.abc.com/')


def test_proxy_aliases():
    with CleanupEtcdFolders(
            ['/upstreams/test-proxy-aliases',
             '/hosts/test-proxy-aliases.abc.com']):
        with MockHttpServer() as node1:
            with MockHttpServer() as node2:
                _add_node('test-proxy-aliases', 'node1', node1)
                _add_location(
                    'test-proxy-aliases.abc.com', 'test-proxy-aliases',
                    aliases={
                        'www': 'www.test-proxy-aliases.abc.com'
                    }
                )
                # Wait for sometime for changes to apply
                sleep(PROXY_REFRESH_TIME)
                resp = _request_proxy('test-proxy-aliases.abc.com')
                assert_equals(resp.status_code, 200)

                resp = _request_proxy('www.test-proxy-aliases.abc.com')
                assert_equals(resp.status_code, 200)


def test_proxy_when_all_upstream_nodes_gets_removed():
    with CleanupEtcdFolders(
            ['/upstreams/test-nodes-removal',
             '/hosts/test-nodes-removal.abc.com']):
        with MockHttpServer() as node1:

            # Given: Proxy with existing nodes
            # First we add nodes
            _add_node('test-nodes-removal', 'node1', node1)
            _add_location('test-nodes-removal.abc.com',
                          'test-nodes-removal')

            # Wait for sometime changes to apply
            sleep(PROXY_REFRESH_TIME)

            # Validate that proxy was setup
            resp = _request_proxy('test-nodes-removal.abc.com')
            assert_equals(resp.status_code, 200)

            # When: I remove the backend nodes
            _remove_node('test-nodes-removal', 'node1', node1)
            # Wait for sometime changes to apply
            sleep(PROXY_REFRESH_TIME)

            # Validate that No BE node is available for servicing request
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
            # Wait for sometime changes to apply
            sleep(PROXY_REFRESH_TIME)

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
            # Wait for sometime changes to apply
            sleep(PROXY_REFRESH_TIME)

            resp = _request_proxy('test-allowed-acl.abc.com')
            assert_equals(resp.status_code, 403)


def test_proxy_with_multiple_locations():
    with CleanupEtcdFolders(
            ['/upstreams/test-multiple-loc',
             '/global/acls/test-multiple-loc-acl1',
             '/hosts/test-multiple-loc.abc.com']):
        with MockHttpServer() as node1:
            _add_node('test-multiple-loc', 'node1', node1)
            _add_acl('test-multiple-loc-acl1', '255.255.255.255/32')
            _add_location('test-multiple-loc.abc.com',
                          'test-multiple-loc', path='/', location_name='-',
                          allowed_acls={'a1': 'test-multiple-loc-acl1'})
            _add_location('test-multiple-loc.abc.com',
                          'test-multiple-loc', path='/secure',
                          location_name='secure',
                          allowed_acls={'public': 'public'})
            # Wait for sometime changes to apply
            sleep(PROXY_REFRESH_TIME)

            # When I access secure path
            resp = _request_proxy('test-multiple-loc.abc.com', path='/secure')

            # Then:  Access is granted (but 404 is returned as page does not
            # exist)
            assert_equals(resp.status_code, 404)

            # When I access un-seure path
            resp = _request_proxy('test-multiple-loc.abc.com', path='/')

            # Then:  Access is denied (No acl to allow this path)
            assert_equals(resp.status_code, 403)
