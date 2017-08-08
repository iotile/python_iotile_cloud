import sys
import json
import mock
import requests
import requests_mock
import unittest2 as unittest

from iotile_cloud.api.connection import Api
from iotile_cloud.stream.data import StreamData


class StreamDataTestCase(unittest.TestCase):

    page = 1

    def setUp(self):
        api = Api(domain='http://iotile.test')
        self.stream_data = StreamData('s--0001', api)
        self.stream_data._data = []

    def _multi_page_callback(self, request, context):
        page = '1'
        url_elements = request.url.split('?')
        if len(url_elements) == 2:
            args = url_elements[1].split('&')
            for nv in args:
                [name, value] = nv.split('=')
                if name == 'page':
                    page = value
        payload = {
            'next': None,
            'count': 3,
            'results': [
                {'timestamp': '20170109T10:00:00', 'value': 10, 'output_value': '1'},
                {'timestamp': '20170109T10:00:01', 'value': 20, 'output_value': '2'},
                {'timestamp': '20170109T10:00:02', 'value': 30, 'output_value': '3'},
            ]
        }
        if page == '1':
            payload['next'] = url_elements[0] + 'page=2'
        context.status_code = 200
        return json.dumps(payload)

    @requests_mock.Mocker()
    def test_single_page_fetch(self, m):
        payload = {
            'next': None,
            'count': 2,
            'results': [
                {'timestamp': '20170109', 'value': 40, 'output_value': '4'},
                {'timestamp': '20170109', 'value': 50, 'output_value': '5'},
            ]
        }
        m.get('http://iotile.test/api/v1/stream/s--0001/data/', text=json.dumps(payload))

        self.assertEqual(len(self.stream_data._data), 0)
        self.stream_data.initialize_from_server(lastn=3)
        self.assertEqual(len(self.stream_data._data), 2)

    @requests_mock.Mocker()
    def test_multi_page_fetch(self, m):
        m.get('http://iotile.test/api/v1/stream/s--0001/data/', text=self._multi_page_callback)

        self.assertEqual(len(self.stream_data._data), 0)
        self.stream_data.initialize_from_server(lastn=6)
        self.assertEqual(len(self.stream_data._data), 6)




