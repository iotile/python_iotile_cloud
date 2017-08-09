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

