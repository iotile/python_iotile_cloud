# IOTile Cloud Python API Package

A python library for interacting with [IOTile Cloud](https://iotile.cloud) Rest API

## Installation

```
# pip install python_iotile_cloud
pip install git+https://github.com/iotile/python_iotile_cloud.git@v0.4.0-alpha
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

For example, say you want to get a list of Organizations or a given Organization
via the https://iotile.cloud/api/v1/org/ API. You can simply:

```
# After calling c.login() or c.set_token()

# Get list of all organizations
my_organizations = c.org.get()
for org in my_organizations['results']:
   print(str(org)
   
# Get a single organization
org = c.org('my-org-slug').get()
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
