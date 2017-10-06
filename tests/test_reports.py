import unittest2 as unittest
import json
import re
import mock
import requests
import requests_mock
from dateutil.parser import parse as dt_parse

from iotile_cloud.utils.gid import *
from iotile_cloud.stream.report import *


class ReportGenerationTestCase(unittest.TestCase):
    _payload1 = {
        'count': 2,
        'results': [
            {'slug': 's--0000-0001--0000-0000-0000-0002--5001'},
            {'slug': 's--0000-0001--0000-0000-0000-0002--5002'},
        ]
    }

    @requests_mock.Mocker()
    def test_source_factories_project(self, m):
        api = Api(domain='http://iotile.test')
        m.get('http://iotile.test/api/v1/stream/?project=p--0000-0001', text=json.dumps(self._payload1))

        rg = BaseReportGenerator(api)
        rg._fetch_streams_from_project_slug('p--0001')
        self.assertEqual(len(rg._streams), 2)

    @requests_mock.Mocker()
    def test_source_factories_project(self, m):
        api = Api(domain='http://iotile.test')

        m.get('http://iotile.test/api/v1/stream/?device=d--0000-0000-0000-0002', text=json.dumps(self._payload1))

        rg = BaseReportGenerator(api)
        rg._fetch_streams_from_device_slug('d--0002')
        self.assertEqual(len(rg._streams), 2)

    @requests_mock.Mocker()
    def test_source_factories_project(self, m):
        api = Api(domain='http://iotile.test')
        payload = {
            'slug': 's--0000-0001--0000-0000-0000-0002--5001'
        }

        m.get('http://iotile.test/api/v1/stream/s--0000-0001--0000-0000-0000-0002--5001/', text=json.dumps(payload))

        rg = BaseReportGenerator(api)
        rg._fetch_stream_from_slug('s--0000-0001--0000-0000-0000-0002--5001')
        self.assertEqual(len(rg._streams), 1)
        self.assertEqual(rg._streams[0]['slug'], 's--0000-0001--0000-0000-0000-0002--5001')
