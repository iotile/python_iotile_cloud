"""A simple mock iotile.cloud server for testing cloud interactions.

This class can be directly instantiated or used as a pytest fixture
with the name mock_cloud.  It requires the following additional package:
 - pytest_localserver

The point of this class is to allow spinning up an API-compatible
iotile.cloud server easily during python testing to allow for:
 - unit testing of routines that directly interact with cloud APIs
 - integration testing of subsystems that depend on data received
   from the cloud to trigger their behavior.

Example usage can be found by looking at:
- tests/test_mock_cloud.py for example invocation
- tests/conftest.py for example fixture setup including populating
  the mock cloud with data.
- tests/data for example mock cloud data

"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import re
import os.path
import json
import csv
import logging

try:
    import pytest
    from pytest_localserver.http import WSGIServer
    from werkzeug.wrappers import Request, Response
except ImportError:
    raise RuntimeError("You must have pytest and pytest_localserver installed to be able to use MockIOTileCloud")


class ErrorCode(Exception):
    def __init__(self, code):
        super(ErrorCode, self).__init__()
        self.status = code


class MockIOTileCloud(object):
    """A test instance of IOTile.cloud for continuous integration."""

    def __init__(self, config_file=None):
        self.logger = logging.getLogger(__name__)

        self.request_count = 0
        self.error_count = 0

        self.apis = []
        self.users = {}
        self.devices = {}
        self.datablocks = {}
        self.streams = {}
        self.properties = {}
        self.projects = {}

        self.events = {}

        self.stream_folder = None

        if config_file is not None:
            self.add_data(config_file)

        self.add_api("/api/v1/auth/login/", self.login)
        self.add_api("/api/v1/account/", self.account)

        # APIs for getting raw data
        self.add_api("/api/v1/stream/(s--[0-9\-a-f]+)/data/", self.get_stream_data)
        self.add_api("/api/v1/event/([0-9]+)/data/", self.get_raw_event)

        # APIs for querying single models
        self.add_api("/api/v1/device/(d--[0-9\-a-f]+)/", lambda x, y: self.one_object('devices', x, y))
        self.add_api("/api/v1/datablock/(b--[0-9\-a-f]+)/", lambda x, y: self.one_object('datablocks', x, y))
        self.add_api("/api/v1/stream/(s--[0-9\-a-f]+)/", lambda x, y: self.one_object('streams', x, y))
        self.add_api("/api/v1/project/([0-9\-a-f]+)/", lambda x, y: self.one_object('projects', x, y))
        self.add_api("/api/v1/vartype/([0-9\-a-zA-Z]+)/", self.get_vartype)

        # APIs for listing models
        self.add_api(r"/api/v1/stream/", self.list_streams)
        self.add_api(r"/api/v1/event/", self.list_events)
        self.add_api(r"/api/v1/property/", self.list_properties)

    def add_api(self, regex, callback):
        """Add an API matching a regex."""

        matcher = re.compile(regex)
        self.apis.append((matcher, callback))

    @classmethod
    def _parse_json(cls, request, *keys):
        data = request.get_data()
        string_data = data.decode('utf-8')

        try:
            injson = json.loads(string_data)

            if len(keys) == 0:
                return injson

            result = []

            for key in keys:
                if key not in injson:
                    raise ErrorCode(400)

                result.append(injson[key])

            return result
        except:
            raise ErrorCode(400)

    def get_vartype(self, request, slug):
        """Get a vartype object."""

        path = os.path.join(self.stream_folder, 'variable_types', '%s.json' % slug)
        if not os.path.isfile(path):
            raise ErrorCode(404)

        try:
            with open(path, "r") as infile:
                vartype = json.load(infile)
        except:
            raise ErrorCode(500)

        return vartype

    def one_object(self, obj_type, request, obj_id):
        """Handle /<object>/<slug>/ GET."""

        self.verify_token(request)

        container = getattr(self, obj_type)
        if obj_id not in container:
            raise ErrorCode(404)

        return container[obj_id]

    def list_streams(self, request):
        """List and possibly filter streams."""

        results = []

        if 'device' in request.args:
            results = [x for x in self.streams.values() if x['device'] == request.args['device']]
        elif 'project' in request.args:
            results = [x for x in self.streams.values() if x['project'] == request.args['project'] or x['project_id'] == request.args['project']]
        elif 'block' in request.args:
            results = [x for x in self.streams.values() if x['block'] == request.args['block']]

        return self._paginate(results, request, 100)

    def list_events(self, request):
        """List and possibly filter events."""

        # No listing of events if there is no filter
        results = []

        if 'filter' in request.args:
            filter_str = request.args['filter']
            if filter_str.startswith('s--'):
                results = [x for x in self.events.values() if x['stream'] == filter_str]
            elif filter_str.startswith('d--'):
                results = [x for x in self.events.values() if x['device'] == filter_str]
            else:
                raise ErrorCode(500)

        return self._paginate(results, request, 100)

    def list_properties(self, request):
        """List properties."""

        # No listing of events if there is no filter
        results = []

        if 'target' in request.args:
            target_str = request.args['target']
            results = [x for x in self.properties.values() if x['target'] == target_str]

        return self._paginate(results, request, 100)

    def get_raw_event(self, request, event_id):
        if self.stream_folder is None:
            raise ErrorCode(404)

        path = os.path.join(self.stream_folder, 'event_%s.json' % event_id)
        if not os.path.isfile(path):
            raise ErrorCode(404)

        with open(path, "r") as infile:
            results = json.load(infile)

        return results

    def get_stream_data(self, request, stream):
        if stream not in self.streams:
            raise ErrorCode(404)

        results = []

        if self.stream_folder is not None:
            json_stream_path = os.path.join(self.stream_folder, stream + '.json')
            csv_stream_path = os.path.join(self.stream_folder, stream + '.csv')

            if os.path.isfile(json_stream_path):
                with open(json_stream_path, "r") as infile:
                    results = json.load(infile)
            elif os.path.isfile(csv_stream_path):
                results = self._format_stream_data(self.streams[stream], csv_stream_path)

        return self._paginate(results, request, 1000)

    def _format_stream_data(self, stream, csvpath):
        results = []

        with open(csvpath, "r") as infile:
            reader = csv.reader(infile)

            for row in reader:
                ts = row[0]
                intval = row[1]

                res = {
                    "type": "ITR",
                    "timestamp": ts,
                    "int_value": intval,
                    "value": intval,
                    "display_value": str(intval),
                    "output_value": intval,
                    "streamer_local_id": None
                }

                results.append(res)

        return results

    def _paginate(self, results, request, default_page_size):
        """Paginate and wrap results."""

        page_size = request.args.get('page_size', default_page_size)
        page = request.args.get('page', 1)

        if not isinstance(page, int):
            page = int(page)

        if not isinstance(page_size, int):
            page_size = int(page_size)

        filtered = results[(page - 1)*page_size: page*page_size]

        # FIXME: Actually include previous and next links
        return {
            u"count": len(results),
            u"previous": None,
            u"next": None,
            u"results": filtered
        }

    def login(self, request):
        """Handle login."""

        user, password = self._parse_json(request, 'email', 'password')

        self.logger.info("User %s, password %s", user, password)
        if user not in self.users:
            raise ErrorCode(401)

        if password != self.users[user]:
            raise ErrorCode(401)

        return {
            'username': user,
            'jwt': "JWT_USER"
        }

    def account(self, request):
        self.verify_token(request)
        return {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "email": "unknown email",
                    "username": "unknown username",
                    "name": "unknown name",
                    "slug": "unknown slug"
                }
            ]
        }

    def verify_token(self, request):
        """Make sure we have the right token for access."""

        auth = request.headers.get('Authorization', None)
        if auth is None or auth != 'jwt JWT_USER':
            raise ErrorCode(401)

    def __call__(self, environ, start_response):
        """Actual callback invoked for urls."""

        req = Request(environ)
        path = environ['PATH_INFO']

        self.request_count += 1

        for matcher, callback in self.apis:
            res = matcher.match(path)
            if res is None:
                continue

            groups = res.groups()
            response_headers = [(b'Content-type', b'application/json')]

            try:
                data = callback(req, *groups)
                if data is None:
                    data = {}

                resp = json.dumps(data)

                resp = Response(resp.encode('utf-8'), status=200, headers=response_headers)
                return resp(environ, start_response)
            except ErrorCode as err:
                self.error_count += 1

                response_headers = [(b'Content-type', b'text/plain')]
                resp = Response(b"Error serving request\n", status=err.status, headers=response_headers)
                return resp(environ, start_response)

        self.error_count += 1

        resp = Response(b"Page not found.", status=404, headers=response_headers)
        return resp(environ, start_response)

    def add_data(self, path):
        """Add data to our mock cloud from a json file."""

        with open(path, "r") as infile:
            data = json.load(infile)

        self.users.update(data.get('users', {}))
        self.devices.update({x['slug']: x for x in data.get('devices', [])})
        self.datablocks.update({x['slug']: x for x in data.get('datablocks', [])})
        self.streams.update({x['slug']: x for x in data.get('streams', [])})
        self.properties.update({x['name']: x for x in data.get('properties', [])})
        self.projects.update({x['id']: x for x in data.get('projects', [])})
        self.events.update({x['id']: x for x in data.get('events', [])})


@pytest.fixture(scope="module")
def mock_cloud():
    """A Mock iotile.cloud instance for testing."""

    cloud = MockIOTileCloud()

    # Generate a new fake, unverified ssl cert for this server
    server = WSGIServer(application=cloud, ssl_context="adhoc")

    server.start()
    domain = server.url
    yield domain, cloud
    server.stop()


@pytest.fixture(scope="module")
def mock_cloud_nossl():
    """A Mock iotile.cloud instance for testing without ssl."""

    cloud = MockIOTileCloud()
    server = WSGIServer(application=cloud)

    server.start()
    domain = server.url
    yield domain, cloud
    server.stop()
