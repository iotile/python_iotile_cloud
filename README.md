# IOTile Cloud Python API Package

[![Build Status](https://travis-ci.org/iotile/python_iotile_cloud.svg?branch=master)](https://travis-ci.org/iotile/python_iotile_cloud)
[![PyPI version](https://img.shields.io/pypi/v/iotile_cloud.svg)](https://pypi.python.org/pypi/iotile-cloud) 


A python library for interacting with [IOTile Cloud](https://iotile.cloud) Rest API

## Installation

When it comes to using Python packages, it is always recommened you use a Python Virtual Env. Using Python 3, you can simply do

```
python3 -m venv  ~/.virtualenv/iotile-cloud
```

or follow the many tutorials on the Web to install `virtualenv` on Python 2.

Once you have set up a virtual, env, simply install the package with:

```
pip install iotile_cloud
```

Package is based on https://github.com/samgiles/slumber

## IOTile Cloud Resource Overview

In a Rest API, Resources represent tables in the database. The following resources are available in **IOTile Cloud**:

- **account**: Represent users. A user only has access to its own user profile
- **org**: Users belong to Organizations as members. Some of these users can act as admins for the organization.
- **porject**: Organizations contain Projects. Projects group information about a given set of devices.
- **device**: A device represents a physical IOTile devices (Like POD-1) or virtual devices
- **variable**: Variables are used to represent the outputs of a device. e.g. If a device has two sensors, you 
may have Variable `IO 1` and `IO 2`.
- **stream**: Streams represent a globally unique instance of data comming from a given sensor. 
- **data**: Every Stream represents the time series data. This resource can be used to access this data.
This API always requires a `?filter=<slug>` to filter the data, where the slud is one of the universally unique global IDs

### Globally Unique IDs

Most of the key records in the database use a universally unique ID, in the form of an ID Slug. We borrow the term slug
from blogging systems because we use it the same way to create unique but readable URLs.

The following are the resources that use a globally unique ID:

- Projects use **p--0000-0001** (Note that project is the one object which the APIs do not use a slug for. Instead, projects require a UUID).
- Variable **v--0000-0001--5001** represent variable 5001 in project 1
- Device **d--0000-0000-0000-0001** represent device 1. Note that this is also the Serial Number for the device itself,
and can be found on each IOTile Device.
- Stream **s--0000-0001--0000-0000-0000-0002--5001** represent variable 5001 for device 2 in project 1.

You can see how:

- Slug components are separated by a ‘--’ string
- A one character letter represents the type of slug: ‘p’, ‘d’, ‘v’ and ‘s’
- Projects are represented with an 8 character HEX number
- Devices are represented with a 16 character HEX number
- Per device Variables are represented with a 4 character HEX number
- Variable Ids are local to a project and therefore require the project ID to globally uniquify them.
- Globally unique streams use project, device and variable IDs


## User Guide


### Login and Logout

The Api class is used to login and logout from the IOTile Cloud

Example:

```
from iotile_cloud.api.connection import Api

c = Api()

ok = c.login(email=args.email, password=password)
if ok:
    # Do something
    
    c.logout()
```

If you have a JWT token, you can skip the login and just set the token:

```
from iotile_cloud.api.connection import Api

c = Api()

c.set_token('big-ugly-token')
```

You can use the Api itself to login and get a token:

```
from iotile_cloud.api.connection import Api

c = Api()

ok = c.login(email=args.email, password=password)
if ok:
    token = c.token
    # write out token or store in some secret .ini file
```

### Generic Rest API

The Api() can be used to access any of the APIs in https://iotile.cloud/api/v1/

The Api() is generic and therefore will support any future resources supported by the IoTile Cloud Rest API.

```
from iotile_cloud.api.connection import Api

api = Api()
ok = api.login(email='user@example.com', password='my.pass')

## GET http://iotile.cloud/api/v1/project/
##     Note: Any kwargs passed to get(), post(), put(), delete() will be used as url parameters
api.org.get()

## POST http://iotile.cloud/api/v1/org/
new = api.org.post({"name": "My new Org"})

## PUT http://iotile.cloud/api/v1/org/{slug}/
api.org(new["slug"]).put({"about": "About Org"})

PATCH http://iotile.cloud/api/v1/org/{slug}/
api.org(new["slug"]).patch({"about": "About new Org"})

## GET http://iotile.cloud/api/v1/org/{slug}/
api.org(new["slug"]).get()

## DELETE http://iotile.cloud/api/v1/org/{slug}/
## NOTE: Not all resources can be deleted by users
api.org(new["slug"]).delete()
```

You can pass arguments to any get() using

```
# /api/v1/org/
for org in c.org.get()['results']:
   # Pass any arguments as get(foo=1, bar='2'). e.g.
   # /api/v1/project/?org__slug=<slug>
   org_projects = c.project.get(org__slug='{0}'.format(org['slug']))

```

You can also call nested resources/actions like this:

```
# /api/v1/org/
for org in c.org.get()['results']:
   # /api/v1/org/<slug>/projects
   org_projects = c.org(org['slug']).projects.get()

```

### Getting Stream Data

You can use `StreamData` to easily download all or partial stream data.

Examples:

```
# After calling c.login() or c.set_token()

stream_id = 's--0000-5555--0000-5555-5555-5555--5555'
stream_data = StreamData(stream_id, c)

# Get last 100 entries
stream_data.initialize_from_server(lastn=100)
for item in stream_data.data:
    print('{0}: {1}'.format(item['timestamp'], item['value']))
    
# Get entries from 2016-1-1 to 2016-1-30 (UTC times are needed)
stream_data.initialize_from_server(start='2016-01-01T00:00:00.000Z' end='2016-01-30T23:00:00.000Z')
```

Or just derive from StreamData. For example, the following script will compute Stats

```
import getpass
import numpy as np
from iotile_cloud.api.connection import Api
from iotile_cloud.stream.data import StreamData


email = 'joe@example.com'
password = getpass.getpass()
stream_id = 's--0000-5555--0000-5555-5555-5555--5555'
lastn = 1000


class MyStreamData(StreamData):

    def analyze(self):
        deltas = []
        for row in self.data:
            deltas.append(row['value'])

        print('==================================')
        print('Count = {0}'.format(len(deltas)))
        print('Mean  = {0}'.format(np.mean(deltas)))
        print('Max   = {0}'.format(np.max(deltas)))
        print('Min   = {0}'.format(np.min(deltas)))
        print('==================================')


ok = c.login(email=email, password=password)
if ok:
    stream_data = MyStreamData(stream_id=stream_id, api=c)
    stream_data.initialize_from_server(lastn=lastn)

    stream_data.analyze()

    c.logout()

```

### User Reports

Package includes a simple utility to generate accumulation reports:

```
from pprint import pprint
from iotile_cloud.api.connection import Api
from iotile_cloud.stream.report import AccumulationReportGenerator

# Generate report for all streams from:
sources = [
    'p--0000-0001', # Project 1
    'd--1111',      # Device 0x111
    's--0000-0002--0000-0000-0000-2222--5001'  # Stream 5001 for device 0x222 in project 2       
]
ok = c.login(email=email, password=password)
if ok:
    gen = AccumulationReportGenerator(c)
    stats = gen.compute_sum(sources=sources, start=t0, end=t1)

    c.logout()
```

Produces:

```
{'streams': {'s--0000-0001--0000-0000-0000-0097--5002': {'sum': 1000.0,
                                                         'units': 'G'},
             's--0000-0001--0000-0000-0000-00a0--5001': {'sum': 1500.0,
                                                         'units': 'G'},
             's--0000-0003--0000-0000-0000-1111--5001': {'sum': 2000.0,
                                                         'units': 'G'},
             's--0000-0002--0000-0000-0000-2222--5001': {'sum': 3000.0,
                                                         'units': 'G'}},
 'total': 7500.0}

```

### Uploading a Streamer Report

Example:

```
from iotile_cloud.api.connection import Api

c = Api()

ok = c.login(email=args.email, password=password)
if ok:
    
    ts = '{}'.format(datetime.datetime.utcnow().isoformat())
    resp = c.streamer(action='report').upload_file(filename='path/to/my/file', timestamp=ts)
```

### Globaly unique ID slugs

To easily handle ID slugs, use the `utils.gid` package:

```
project = IOTileProjectSlug(5)
assert(str(project) == 'p--0000-0005')

device = IOTileDeviceSlug(10)
assert(str(device) == 'd--0000-0000-0000-000a')

variable = IOTileVariableSlug('5001', project)
assert(str(variable) == 'v--0000-0005--5001')

id = IOTileStreamSlug()
id.from_parts(project=project, device=device, variable=variable)
assert(str(id) == 's--0000-0005--0000-0000-0000-000a--5001')

parts = id.get_parts()
self.assertEqual(str(parts['project']), str(project))
self.assertEqual(str(parts['device']), str(device))
self.assertEqual(str(parts['variable']), str(variable))

# Other forms of use
device = IOTileDeviceSlug('000a)
assert(str(device) == 'd--0000-0000-0000-000a')
device = IOTileDeviceSlug(d--000a)
assert(str(device) == 'd--0000-0000-0000-000a')
device = IOTileDeviceSlug(0xa)
assert(str(device) == 'd--0000-0000-0000-000a')
```

### BaseMain Utility Class

As you can see from the examples above, every script is likely to follow the following format:

```
# Parse arguments from user and get password
# Login to server
# Do some real work
# Logout
```

To make it easy to add this boilerplate code, the BaseMain can be used to follow a predefined, opinionated flow
which basically configures the `logging` and `argsparse` python packages with a basic configuration during the 
construction. Then the `main()` method runs the following flow, where each function call can be overwritten in your
own derived class


```
   self.domain = self.get_domain()
   self.api = Api(self.domain)
   self.before_login()
   ok = self.login()
   if ok:
       self.after_login()
       self.logout()
       self.after_logout()
```

An example of how to use this class is shown below:

```
class MyScript(BaseMain):

    def add_extra_args(self):
        # Add extra positional argument (as example)
        self.parser.add_argument('foo', metavar='foo', type=str, help='RTFM')

    def before_login(self):
        logger.info('-----------')

    def after_login(self):
        # Main function to OVERWITE and do real work
        do_some_real_work(self.api, self.args)

    def login(self):
        # Add extra message welcoming user
        ok = super(MyScript, self).login()
        if ok:
            logger.info('Welcome {0}'.format(self.args.email))
        return ok

    def logout(self):
        # Add extra message to say Goodbye
        super(MyScript, self).logout()
        logger.info('Goodbye!')


if __name__ == '__main__':

    work = MyScript()
    work.main()
```

### Misc Utilities

#### MdoHelper (advance)

IOTile Cloud assumes data is transformed in multiple places using a simple Multiple, Divide and Offset (or MDO) 
set of values. For example, streams use output_units, which include an MDO that can be used to convert the 
internal value stored on the data stream into this output unit. The MdoHelper is a simple class to help with these
converstions.

```
from iotile_cloud.stream.data import StreamData
from iotile_cloud.utils.mdo import MdoHelper

stream = api.stream('s--0000-0001--0000-0000-0000-0001--5001').get()
units = stream['output_unit']
mdo = MdoHelper(m=units.get('m', 1), d=units.get('d', 1), o=units.get('o', 0.0))

# Get unmodified internal data. The 'value' member is based on some internal storage units for the given stream type
stream_data = StreamRawData(stream['slug'], api)

stream_data.initialize_from_server(lastn=100)
for item in stream_data.data:
    print('{0}: {1}'.format(item['timestamp'], mdo.compute_value(item['value'])))
```

## Requirements

iotile_cloud requires the following modules.

    * Python 2.7+ or 3.4+
    * requests
    * python-dateutil
    
## Development

To test, run `python setup.py test` or to run coverage analysis:

```
coverage run --source=iotile_cloud setup.py test
coverage report -m
```

## Deployment

To deploy to pypi:

1. Update `version.py` with new version number
1. Update `CHANGELOG.md` with description of new release
1. Run `python setup.py test` to ensure everything is ok
1. Commit all changes to master (PR is needed)
1. Once everythin commited, create a new version Tag. Deployment is triggered from that.
