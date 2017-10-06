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

