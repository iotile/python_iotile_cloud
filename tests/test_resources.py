import sys
import json
import mock
import requests
import requests_mock
import unittest2 as unittest

from iotile_cloud.api.connection import Api, RestResource
from iotile_cloud.api import exceptions


class ResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.base_resource = RestResource(base_url="http://iotile.test/api/v1/test/",
                                          use_token=True,
                                          token_type='jwt',
                                          token='my-token')

    def test_url(self):

        url = self.base_resource.url()
        self.assertEqual(url, 'http://iotile.test/api/v1/test/')

    def test_headers(self):
        expected_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'jwt my-token'
        }

        headers = self.base_resource._get_header()
        self.assertEqual(headers, expected_headers)

    @requests_mock.Mocker()
    def test_get_200(self, m):
        payload = {
            "result": ["a", "b", "c"]
        }
        m.get('http://iotile.test/api/v1/test/', text=json.dumps(payload))

        resp = self.base_resource.get()
        self.assertEqual(resp['result'], ['a', 'b', 'c'])

