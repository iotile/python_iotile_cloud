import sys
import json
import mock
import requests
import requests_mock
import unittest2 as unittest

from iotile_cloud.api.connection import Api, RestResource
from iotile_cloud.api import exceptions


class ApiTestCase(unittest.TestCase):

    def test_init(self):

        api = Api()
        self.assertEqual(api.domain, 'https://iotile.cloud')
        self.assertEqual(api.base_url, 'https://iotile.cloud/api/v1')
        self.assertTrue(api.use_token)
        self.assertEqual(api.token_type, 'jwt')

    @requests_mock.Mocker()
    def test_login(self, m):
        payload = {
            'jwt': 'big-token',
            'username': 'user1'
        }
        m.post('http://iotile.test/api/v1/auth/login/', text=json.dumps(payload))

        api = Api(domain='http://iotile.test')
        ok = api.login(email='user1@test.com', password='pass')
        self.assertTrue(ok)
        self.assertEqual(api.token, 'big-token')

    @requests_mock.Mocker()
    def test_get_list(self, m):
        payload = {
            "result": ["a", "b", "c"]
        }
        m.get('http://iotile.test/api/v1/test/', text=json.dumps(payload))

        api = Api(domain='http://iotile.test')
        resp = api.test.get()
        self.assertEqual(resp['result'], ['a', 'b', 'c'])

    @requests_mock.Mocker()
    def test_get_detail(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://iotile.test/api/v1/test/my-detail/', text=json.dumps(payload))

        api = Api(domain='http://iotile.test')
        resp = api.test('my-detail').get()
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_get_detail_with_action(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://iotile.test/api/v1/test/my-detail/action/', text=json.dumps(payload))

        api = Api(domain='http://iotile.test')
        resp = api.test('my-detail', action='action').url()
        self.assertEqual(resp, 'http://iotile.test/api/v1/test/my-detail/action/')
        resp = api.test('my-detail', action='action').get()
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_get_detail_with_extra_args(self, m):
        payload = {
            "a": "b",
            "c": "d"
        }
        m.get('http://iotile.test/api/v1/test/my-detail/', text=json.dumps(payload))

        api = Api(domain='http://iotile.test')
        resp = api.test('my-detail').url(args='foo=bar')
        self.assertEqual(resp, 'http://iotile.test/api/v1/test/my-detail/?foo=bar')
        resp = api.test('my-detail').get(extra='foo=bar')
        self.assertEqual(resp, {'a': 'b', 'c': 'd'})

    @requests_mock.Mocker()
    def test_post(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.post('http://iotile.test/api/v1/test/', text=json.dumps(result))

        api = Api(domain='http://iotile.test')
        resp = api.test.post(payload)
        self.assertEqual(resp['id'], 1)

    @requests_mock.Mocker()
    def test_patch(self, m):
        payload = {
            "foo": ["a", "b", "c"]
        }
        result = {
            "id": 1
        }
        m.patch('http://iotile.test/api/v1/test/my-detail/', text=json.dumps(result))

        api = Api(domain='http://iotile.test')
        resp = api.test('my-detail').patch(payload)
        self.assertEqual(resp['id'], 1)










