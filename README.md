# IOTile Cloud Python API Package

[![Build Status](https://travis-ci.org/iotile/python_iotile_cloud.svg?branch=master)](https://travis-ci.org/iotile/python_iotile_cloud)
[![PyPI version](https://img.shields.io/pypi/v/iotile_cloud.svg?maxAge=2592000)](https://pypi.python.org/pypi/iotile-cloud) 


A python library for interacting with [IOTile Cloud](https://iotile.cloud) Rest API

## Installation

```
pip install python_iotile_cloud
```

Package is based on https://github.com/samgiles/slumber

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

You can pass arguments to any get using

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
            d1 = row['value']

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

### Uploading a Streamer Report

Example:

```
from iotile_cloud.api.connection import Api

c = Api()

ok = c.login(email=args.email, password=password)
if ok:
    
    url_args = 'timestamp={}'.format(datetime.datetime.utcnow().isoformat())
    resp = c.streamer(action='report').upload_file(filename='path/to/my/file', extra=url_args)
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
