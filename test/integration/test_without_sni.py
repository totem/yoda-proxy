
from . import setup_yoda, destroy_yoda, set_etcd_key, MockHttpServer, \
    ETCD_PROXY_BASE, ETCDCTL, HTTP_TEST_TIMEOUT
from nose.tools import assert_raises, assert_equals
from subprocess import call, check_call
import requests

from time import sleep

from urllib2 import urlopen, HTTPError


__author__ = 'sukrit'


def setup_module():
    #setup_yoda()
    pass


def teardown_module():
    #destroy_yoda()
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
    with MockHttpServer() as node1:
        with MockHttpServer() as node2:
            #requests.get('http://'+node1, timeout=HTTP_TEST_TIMEOUT)
            set_etcd_key('/upstreams/myapp.abc.com-v1/endpoints/node1', node1)
            set_etcd_key('/upstreams/myapp.abc.com-v1/endpoints/node1', node2)
            set_etcd_key('/hosts/myapp.abc.com/locations/home/acls/allowed/a1',
                         'public')
            set_etcd_key('/hosts/myapp.abc.com/locations/home/acls/denied/d1',
                         'global-black-list')
            set_etcd_key('/hosts/myapp.abc.com/locations/home/path', '/')
            set_etcd_key('/hosts/myapp.abc.com/locations/home/force-ssl', False)
            set_etcd_key('/hosts/myapp.abc.com/locations/home/upstream',
                         'myapp.abc.com-v1')

            #Wait 5s for changes to apply
            sleep(5)
            requests.get('http://localhost', timeout=HTTP_TEST_TIMEOUT,
                         headers = {
                             'Host': 'myapp.abc.com'
                         }, verify=False)
    pass