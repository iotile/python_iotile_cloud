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
import datetime
import csv
import logging
import uuid
import iotile_cloud.utils.gid as gid

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

    DEFAULT_ORG_NAME = 'Quick Test Org'
    DEFAULT_ORG_SLUG = 'quick-test-org'

    def __init__(self, config_file=None):
        self.logger = logging.getLogger(__name__)

        self._config_file = config_file
        self.reset()

        self.apis = []
        self._add_api(r"/api/v1/auth/login/", self.login)
        self._add_api(r"/api/v1/account/", self.account)

        # APIs for getting raw data
        self._add_api(r"/api/v1/stream/(s--[0-9\-a-f]+)/data/", self.get_stream_data)
        self._add_api(r"/api/v1/event/([0-9]+)/data/", self.get_raw_event)

        # APIs for querying single models
        self._add_api(r"/api/v1/device/(d--[0-9\-a-f]+)/", lambda x, y: self.one_object('devices', x, y))
        self._add_api(r"/api/v1/datablock/(b--[0-9\-a-f]+)/", lambda x, y: self.one_object('datablocks', x, y))
        self._add_api(r"/api/v1/stream/(s--[0-9\-a-f]+)/", lambda x, y: self.one_object('streams', x, y))
        self._add_api(r"/api/v1/streamer/(t--[0-9\-a-f]+)/", lambda x, y: self.one_object('streamers', x, y))
        self._add_api(r"/api/v1/fleet/(g--[0-9\-a-f]+)/devices/", self.get_fleet_members)
        self._add_api(r"/api/v1/fleet/(g--[0-9\-a-f]+)/", lambda x, y: self.one_object('fleets', x, y))
        self._add_api(r"/api/v1/project/([0-9\-a-f]+)/", lambda x, y: self.one_object('projects', x, y))
        self._add_api(r"/api/v1/org/([0-9\-a-z]+)/", lambda x, y: self.one_object('orgs', x, y))
        self._add_api(r"/api/v1/vartype/([0-9\-a-zA-Z]+)/", self.get_vartype)

        # APIs for listing models
        self._add_api(r"/api/v1/stream/", self.list_streams)
        self._add_api(r"/api/v1/event/", self.list_events)
        self._add_api(r"/api/v1/property/", self.list_properties)
        self._add_api(r"/api/v1/streamer/", self.list_streamers)
        self._add_api(r"/api/v1/device/", self.list_devices)
        self._add_api(r"/api/v1/fleet/", self.list_fleets)

    def reset(self):
        """Clear any stored data in in this cloud as if we created a new instance."""

        self.request_count = 0
        self.error_count = 0

        self.users = {}
        self.devices = {}
        self.datablocks = {}
        self.streams = {}
        self.properties = {}
        self.projects = {}
        self.orgs = {}
        self.fleets = {}
        self.fleet_members = {}
        self.streamers = {}

        self.events = {}

        self.stream_folder = None

        if self._config_file is not None:
            self.add_data(self._config_file)

    def _add_api(self, regex, callback):
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

    def get_fleet_members(self, request, slug):
        if slug not in self.fleets:
            raise ErrorCode(404)

        members = self.fleet_members[slug]
        results = [{'device': x[0], 'is_access_point': x[1], 'always_on': x[2]} for x in members.values()]

        return self._paginate(results, request, 100)

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

    def list_devices(self, request):
        """List and possibly filter devices."""

        results = []
        if 'project' in request.args:
            results = [x for x in self.devices.values() if x['project'] == request.args['project']]
        else:
            results = [x for x in self.devices.values()]

        return self._paginate(results, request, 100)

    def list_fleets(self, request):
        """List and possibly filter fleets."""

        results = []

        if 'device' in request.args:
            slug = request.args['device']
            results = [self.fleets[key] for key, value in self.fleet_members.items() if slug in value]
        else:
            results = [x for x in self.fleets.values()]

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

    def list_streamers(self, request):
        """List and possibly filter streamers."""

        results = []
        
        device_slug = request.args.get('device')
        if device_slug is not None:
            results = [x for x in self.streamers.values() if x['device'] == device_slug]
        else:
            results = [x for x in self.streamers.values()]

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

    def _find_unique_slug(self, slug_type, current_slugs):
        """Generate a unique slug of the given type.

        Type should be 'p', 'd', etc. corresponding to the first
        letter of the slug.
        """

        slug_types = {
            'p': gid.IOTileProjectSlug,
            'd': gid.IOTileDeviceSlug,
            'g': gid.IOTileFleetSlug
        }

        slug_obj = slug_types.get(slug_type)
        if slug_obj is None:
            raise ValueError("Unknown slug type: %s" % slug_type)

        guess = len(current_slugs)
        guess_slug = str(slug_obj(guess))

        while guess_slug in current_slugs:
            guess += 1
            guess_slug = str(slug_obj(guess))

        return guess_slug, guess

    def quick_add_project(self, name=None, org_slug=None):
        """Quickly create an empty default project and add it to the mock cloud.
    
        The project will be added under the quick-test-org organization, which
        is automatically created if it doesn't exist unless you specify a different
        organization explicitly.

        Args:
            name (str): Optional label for the project.
            org_slug (str): Optional slug to create this project under a specific
                org.  The org must exist if you specify it explicitly.  Otherwise
                the project will be created under the default quick-test-org.

        Returns:
            (str, str): The new project id and slug that were added.  Note that this function returns
                a UUID and a slug since both are important for projects.
        """

        known_projects = set([x['slug'] for x in self.projects.values()])

        slug, _numerical_id = self._find_unique_slug('p', known_projects)
        
        if org_slug is None:
            org_slug = self._ensure_quicktest_org()

        if org_slug not in self.orgs:
            raise ValueError("Attempted to add a project to an org that does not exist, slug: %s" % org_slug)

        if name is None:
            name = "Autogenerated Project %d" % (len(self.projects) + 1,)

        proj_id = str(uuid.uuid4())

        proj_data = {
            "id": proj_id,
            "name": name,
            "slug": slug,
            "gid": slug[3:],
            "org": org_slug,
            "about": "",
            "project_template": "default-template-v1-0-0",
            "created_on": self._fixed_utc_timestr(),
            "craeted_by": "quick_test_user"
        }

        self.projects[proj_id] = proj_data
        return proj_id, slug

    def quick_add_org(self, name, slug=None):
        """Quickly add a new org.

        Orgs are just groups of projects so all you need to
        provide is a name for what it should be called and
        the resulting slug to reference when creating a project
        will be returned.

        Args:
            name (str): The name of the organization to add.  The
                name of the organization must contain only letters,
                numbers and spaces.  It must not contain any
                non-alphanumeric characters unless you specify an
                org slug explicitly.

            slug (str): Optional slug of the org.  Autogenerated
                if not given.

        Returns:
            str: The slug of the created organization
        """

        if slug is None:
            slug = name.lower().replace(' ', '-')

        if slug in self.orgs:
            raise ValueError("Attempted to add a duplicate organization")

        org_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "slug": slug,
            "about": "",
            "created_on": self._fixed_utc_timestr(),
            "created_by": "quick_test_user",
            "avatar": {
                "tiny": None,
                "thumbnail": None
            }
        }

        self.orgs[slug] = org_data
        return slug

    def quick_add_user(self, email="test@arch-iot.com", password="test"):
        """Quickly add a user.

        The default arguments if none are specified will add a single user:
        test@arch-iot.com with password "test"

        Args:
            email (str): The user's email address
            password (str): The user's password
        """

        if email in self.users:
            raise ValueError("User already exists, email: %s" % email)

        self.users[email] = password

    def quick_add_device(self, project_id, device_id=None, streamers=None):
        """Quickly add a device to the given project.

        You can optionally specify a list of integers which will be used
        to initialize the cloud acknowledgment values for those streamers
        on this device.

        Args:
            project_id (str): The string uuid of the project you want to 
                add this device to.
            device_id (int or str): The device id or slug to add.  
                If this is not specified, a new unique id is allocated.
            streamers (list of int): A list of streamer acknowledgement values
                to initialize the cloud with.

        Returns:
            str: The device slug that was created.
        """
    
        if project_id not in self.projects:
            raise ValueError("Unknown project id: %s" % project_id)

        if device_id is None:
            slug, device_id = self._find_unique_slug('d', set(self.devices.keys()))
        else:
            slug_obj = gid.IOTileDeviceSlug(device_id)
            slug = str(slug_obj)
            device_id = slug_obj.get_id()

        if streamers is None:
            streamers = []

        if slug in self.devices:
            raise ValueError("Attempted to add a duplicate device slug: %s" % slug)

        dev_info = {
            "id": device_id,
            "slug": slug,
            "gid": slug[3:],
            "label": "Unnamed device %d" % (len(self.devices) + 1,),
            "active": True,
            "external_id": "",
            "sg": "water-meter-v1-1-0",
            "template": "internaltestingtemplate-v0-1-0",
            "org": "arch-internal",
            "project": project_id,
            "lat": None,
            "lon": None,
            "created_on": self._fixed_utc_timestr(),
            "claimed_by": "quick_test_user",
            "claimed_on": self._fixed_utc_timestr()
        }

        self.devices[slug] = dev_info

        for i, ack in enumerate(streamers):
            self.quick_add_streamer(slug, i, ack)

        return slug

    def quick_add_streamer(self, device_id, streamer_index, streamer_ack, selector=None):
        """Add a streamer record for a device and streamer combination.

        Streamer records store a "sequence number" for the last reading 
        received from a device selected by a fixed selection criteria.  
        As of writing time, devices can have up to 8 streamers numbered 0-7.

        Each streamer is an independent channel over which to safely transmit
        readings to the cloud.  Each streamer has an independent streamer record.
        
        Args:
            device_id (int or str): The device id or slug that we are adding
                a streamer record for.
            streamer_index (int): The streamer index for the record we are adding
            streamer_ack (int): The highest reading id we want to claim is
                acknowledged by the cloud.
            selector (int): Optional selector criteria used by this streamer.  If this
                is specified it is used as is.  If not, the default selector for each
                index is used.
        """

        default_selectors = {
            0: 0xd7ff,
            1: 0x5fff
        }

        streamer_index = int(streamer_index)
        streamer_ack = int(streamer_ack)

        if selector is None:
            selector = default_selectors.get(streamer_index)
        
        if selector is None:
            selector = 0xFFFF

        streamer_slug_obj = gid.IOTileStreamerSlug(device_id, streamer_index)
        device_slug = streamer_slug_obj.get_device()
        streamer_slug = str(streamer_slug_obj)
        
        streamer_data = {
            "id": len(self.streamers) + 1,
            "slug": streamer_slug,
            "device": device_slug,
            "index": streamer_index,
            "last_id": streamer_ack,
            "last_reboot_ts": self._fixed_utc_timestr(),
            "is_system": bool(selector != 0xFFFF and (selector & (1 << 11))),
            "selector": selector
        }

        self.streamers[streamer_slug] = streamer_data

    def quick_add_fleet(self, devices, is_network=False, fleet_slug=None, org_slug=None):
        """Quickly add a fleet.

        A fleet is a group of devices.  A device can be in many fleets.  Fleets have a 
        single property, is_network which determines whether they should be considered
        for gateway management.  

        You should create a fleet with a list of devices.  For each device you can
        pass either an integer id, slug of IOTileDeviceSlug object.  If you want to
        mark the device as an access point for the fleet, you can pass a tuple
        with (id_like, access_point, always_on) instead of just an id_like for that device.
        If you don't pass access point, it defaults to False.  If you don't pass always_on
        it defaults to True. 

        Args:
            device (list of id_like or (id_like, bool)): A list of the devices that should
                be in this network.  You need to pass an id_like which can be an integer,
                string of IOTileDeviceSlug object.  If you want to mark the device as an
                access_point for the fleet, pass a tuple with (id_like, True) for that
                entry of the list.
            is_network (bool): Whether this fleet should be considered for gateway management
                or if its just a group of devices.
            fleet_slug (str, int or IOTileFleetSlug): An optional explicit slug for the fleet.
            org_slug (str): An optional explicit slug for the owning org of the fleet.  If
                not specified, it defaults to DEFAULT_ORG_SLUG.

        Returns:
            str: The slug of the newly created fleet.
        """

        device_entries = []
        for dev in devices:
            access = False
            always_on = True
            if isinstance(dev, tuple):
                if len(dev) == 2:
                    dev, access = dev
                elif len(dev) == 3:
                    dev, access, always_on = dev
                else:
                    raise ValueError("Invalid tuple for device that does not contain 2 or 3 items")

            dev_slug_obj = gid.IOTileDeviceSlug(dev)
            dev_slug = str(dev_slug_obj)
            if dev_slug not in self.devices:
                raise ValueError("Unknown device specified in fleet, slug: %s" % dev_slug)

            device_entries.append((str(dev_slug), access, always_on))

        if fleet_slug is None:
            fleet_slug, _unused = self._find_unique_slug('g', set(self.fleets.keys()))

        if fleet_slug in self.fleets:
            raise ValueError("Fleet already exists with given slug: %s" % fleet_slug)

        if org_slug is None:
            org_slug = self._ensure_quicktest_org()

        if org_slug not in self.orgs:
            raise ValueError("Unkown org slug specified for fleet, slug: %s" % org_slug)

        fleet_data = {
            "id": len(self.fleets) + 1,
            "name": "Unnamed Fleet %d" % (len(self.fleets) + 1,),
            "slug": fleet_slug,
            "org": org_slug,
            "description": "",
            "created_on": self._fixed_utc_timestr(),
            "created_by": "quick_test_user",
            "is_network": bool(is_network)
        }

        self.fleets[fleet_slug] = fleet_data
        self.fleet_members[fleet_slug] = {x[0]: x for x in device_entries}
        return fleet_slug

    def _fixed_utc_timestr(self):
        """Create an unchanging utc timestring that is timezone aware."""

        return datetime.datetime(2018, 1, 1).isoformat() + 'Z'

    def _ensure_quicktest_org(self):
        """Ensure that the quick-test-org org is added."""

        if self.DEFAULT_ORG_SLUG not in self.orgs:
            self.quick_add_org(self.DEFAULT_ORG_NAME, slug=self.DEFAULT_ORG_SLUG)

        return self.DEFAULT_ORG_SLUG


@pytest.fixture(scope="module")
def mock_cloud():
    """A Mock iotile.cloud instance for testing with ssl."""

    cloud = MockIOTileCloud()

    # Generate a new fake, unverified ssl cert for this server
    server = WSGIServer(application=cloud, ssl_context="adhoc")

    server.start()
    domain = server.url
    yield domain, cloud
    
    cloud.reset()
    server.stop()


@pytest.fixture(scope="module")
def mock_cloud_nossl():
    """A Mock iotile.cloud instance for testing without ssl."""

    cloud = MockIOTileCloud()
    server = WSGIServer(application=cloud)

    server.start()
    domain = server.url
    yield domain, cloud

    cloud.reset()
    server.stop()


@pytest.fixture(scope="function")
def mock_cloud_private(mock_cloud):
    """A Mock cloud instance that is reset after each test function with ssl."""

    domain, cloud = mock_cloud

    cloud.reset()
    yield domain, cloud
    cloud.reset()


@pytest.fixture(scope="function")
def mock_cloud_private_nossl(mock_cloud_nossl):
    """A Mock cloud instance that is reset after each test function without ssl."""

    domain, cloud = mock_cloud_nossl

    cloud.reset()
    yield domain, cloud
    cloud.reset()
