### v0.9.10 (2019-07-31)

  * Optional Api timeout parameter

### v0.9.9 (2018-12-13)

  * Fix login. It is now possible to log in after logout.

### v0.9.8 (2018-11-08)

  * mock hooks updated for OTA

### v0.9.7 (2018-10-29)

  * Sort stability for ota ID assignment

### v0.9.6 (2018-10-26)

  * Support for mock OTA and generated report endpoints

### v0.9.5 (2018-09-13)

  * Support for Virtual Streams where Device is 0 (or None)

### v0.9.4 (2018-06-26)

  * Fix msgpack decoding on python 3.  It should pass raw=False to properly
    decode string keys as unicode objects.

### v0.9.3 (2018-05-27)

  * Enhance upload_file to accept a data payload on top of the file for a
    multipart file upload.

### v0.9.2 (2018-04-24)

  * Add support for mocking /api/v1/device/<slug>/extra/ API that will count
    data points in streams and return their slugs even if there is no stream_id
    object for the stream data.

### v0.9.1 (2018-04-17)

  * Fix /api/v1/df API to properly return csv data when requested with the
    correct Accept header or format.

### v0.9.0 (2018-04-10)

  * Drop support for Python v3.4 and v3.5
  * Update mock_cloud to properly parse integers loaded from a csv file.

### v0.8.13 (2018-03-28)

  * Allow IOTileStreamSlug to take a project that is None or ''

### v0.8.12 (2018-03-07)

  * Fix typo in IOTileProjectSlug preventing `p--0000-0000` from been accepted as valid.
  * Allow delete() to accept data

### v0.8.11 (2018-03-04)

  * Change IOTileDeviceSlug back to accepting 64bits by default, but add a new allow_64bits option to be turned off
  if required to enforce 48bit checks

### v0.8.10 (2018-03-02)

  * Fix bug and missing tests in IOTileFleetSlug

### v0.8.9 (2018-03-02)

  * Explicitly check for upper limits for the different IOTileCloudSlug IDs

### v0.8.8 (2018-03-02)

  * Better testing of IOTileCloudSlug corner cases
  * Add `future` package to make utils.gid python2 friendly

### v0.8.7 (2018-03-02)

  * Ensure IOTileDeviceSlug only considers 48 bits when converting formatted ids
  
### v0.8.6 (2018-02-27)

  * Allow params to be passed to POST, PATCH, PUT and DELETE

### v0.8.5 (2018-02-23)

  * Fix get stream acknowledgment to get the right dictionary field (Issue #28)

### v0.8.4

  * Add support for PATCH in API

### v0.8.3 (2018-02-06)

  * Add support for `api/v1/data/?filter=` and `api/v1/df/?filter=` APIs.
  * Build IOTileProjectSlug if needed when constructing an IOTileVariableSlug

### v0.8.2 (2018-01-27)

  * Add support for uploading reports using /streamer/report/ api, keeping
    the raw report around along with a record of when it was uploaded.

### v0.8.1 (2018-01-26)

  * Fix import error that broke pytest if you did not have pytest-localserver
    installed, even if you didn't try to use mock_cloud.

### v0.8.0 (2018-01-26)

  * Add utils.mock_cloud module to allow for testing python functions that depend on cloud apis
  * Register two pytest fixtures using the mock cloud: mock_cloud and mock_cloud_nossl

### v0.7.3 (2017-11-29)

  * Add utils.mdo.MdoHelper class to help with raw stream data conversions

### v0.7.2 (2017-11-02)

  * Allow users to specify a verify=False option in Api() that disabled SSL certificate verification for iotile.cloud
  * Allow IOTileCloudStreamSlug.from_parts to accept non-IOTileCloud*Slug object arguments

### v0.7.1 (2017-10-27)
  
  * Adds a BaseMain Class to be used to reduce boiler plate code when writing scripts.
  * Helps configure the logging and argument parsing.

### v0.7.0 (2017-10-05)

  * New data.report.AccumulationReportGenerator to compute sums across projects, devices and/or streams
  * Allow set_token to switch token_type

### v0.6.5 (2017-09-10)

  * Fixes deployment issue

### v0.6.4 (2017-09-10)

  * Add missing package to setup.py

### v0.6.3 (2017-09-10)

  * Add IOTileCloudSlug.get_id() to convert slug back to an id when appropriate
  * Add IOTileBlockSlug() for DataBlock Slugs
  
### v0.6.2 (2017-09-08)

  * New `utils.gid` API to process ID Slugs
  
### v0.6.1 (2017-08-08)

  * Make sure StreamData._data is always cleared when calling constructor or inialization function
  
### v0.6.0 (2017-08-06)

  * Improved StreamData, now supporting any filtering options
  * New RawData for easy quering of the /api/v1/data/ API
  
### v0.5.2 (2017-05-10)

  * Add Api function to refresh token
  
### v0.5.0 (2017-02-06)

  * Changes to API to better handle nested resource actions and API arguments.
     * Old: api.org(action='projects').get(extra='a=1&b=2')
     * New api.org().projects.get(a=1, b=2)
  
### v0.4.3 (2017-02-05)

  * Add python-dateutil dependency
  
### v0.4.2 (2017-02-05)

  * First release from CI server

### v0.4.1 (2017-02-05)

  * First release on PyPI

### v0.4.0 (2017-02-04)

  * First Public Version

