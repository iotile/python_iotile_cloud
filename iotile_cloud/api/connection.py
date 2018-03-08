"""
See https://gist.github.com/dkarchmer/d85e55f9ed5450ba58cb
This API generically supports DjangoRestFramework based APIs
It is based on https://github.com/samgiles/slumber, but customized for
Django Rest Frameworks, and the use of TokenAuthentication.
Usage:
    # Assuming
    # v1_api_router.register(r'some_model', SomeModelViewSet)
    api = Api('http://127.0.0.1:8000')
    api.login(email='user1@test.com', password='user1')
    obj_list = api.some_model.get()
    logger.debug('Found {0} groups'.format(obj_list['count']))
    obj_one = api.some_model(1).get()
    api.logout()
"""
import json
import requests
import logging
from .exceptions import *

DOMAIN_NAME = 'https://iotile.cloud'
API_PREFIX = 'api/v1'
DEFAULT_HEADERS = {'Content-Type': 'application/json'}
DEFAULT_TOKEN_TYPE = 'jwt'

logger = logging.getLogger(__name__)


class RestResource(object):
    """
    Resource provides the main functionality behind a Django Rest Framework based API. It handles the
    attribute -> url, kwarg -> query param, and other related behind the scenes
    python to HTTP transformations. It's goal is to represent a single resource
    which may or may not have children.
    """

    def __init__(self, *args, **kwargs):
        self._store = kwargs
        if 'use_token' not in self._store:
            self._store['use_token'] = False
        if 'verify' not in self._store:
            self._store['verify'] = True

    def __call__(self, id=None):
        """
        Returns a new instance of self modified by one or more of the available
        parameters. These allows us to do things like override format for a
        specific request, and enables the api.resource(ID).get() syntax to get
        a specific resource by it's ID.
        """

        kwargs = {
            'token': self._store['token'],
            'use_token': self._store['use_token'],
            'token_type': self._store['token_type'],
            'base_url': self._store['base_url'],
            'verify': self._store['verify']
        }

        new_url = self._store['base_url']
        if id is not None:
            new_url = '{0}{1}/'.format(new_url, id)

        if not new_url.endswith('/'):
            new_url += '/'

        kwargs['base_url'] = new_url

        return self._get_resource(**kwargs)

    def __getattr__(self, item):
        # Don't allow access to 'private' by convention attributes.
        if item.startswith("_"):
            raise AttributeError(item)

        kwargs = self._copy_kwargs(self._store)
        kwargs.update({'base_url': '{0}{1}/'.format(self._store["base_url"], item)})

        return self._get_resource(**kwargs)

    def _copy_kwargs(self, dictionary):
        kwargs = {}
        for key, value in self._iterator(dictionary):
            kwargs[key] = value

        return kwargs

    def _iterator(self, d):
        """
        Helper to get and a proper dict iterator with Py2k and Py3k
        """
        try:
            return d.iteritems()
        except AttributeError:
            return d.items()

    def _check_for_errors(self, resp, url):

        if 400 <= resp.status_code <= 499:
            exception_class = HttpNotFoundError if resp.status_code == 404 else HttpClientError
            error_msg = 'Client Error {0}: {1}'.format(resp.status_code, url)
            if resp.status_code == 400 and resp.content:
                error_msg += ' ({0})'.format(resp.content)
            raise exception_class(error_msg, response=resp, content=resp.content)
        elif 500 <= resp.status_code <= 599:
            raise HttpServerError("Server Error %s: %s" % (resp.status_code, url), response=resp, content=resp.content)

    def _handle_redirect(self, resp, **kwargs):
        # @@@ Hacky, see description in __call__
        resource_obj = self(url_override=resp.headers["location"])
        return resource_obj.get(**kwargs)

    def _try_to_serialize_response(self, resp):
        if resp.status_code in [204, 205]:
            return

        if resp.content:
            if type(resp.content) == bytes:
                try:
                    encoding = requests.utils.guess_json_utf(resp.content)
                    return json.loads(resp.content.decode(encoding))
                except Exception:
                    return resp.content
            return json.loads(resp.content)
        else:
            return resp.content

    def _process_response(self, resp):

        self._check_for_errors(resp, self.url())

        if 200 <= resp.status_code <= 299:
            return self._try_to_serialize_response(resp)
        else:
            return  # @@@ We should probably do some sort of error here? (Is this even possible?)

    def url(self):
        url = self._store["base_url"]
        return url

    def _get_header(self):
        headers = DEFAULT_HEADERS
        if self._store['use_token']:
            if not "token" in self._store:
                raise RestBaseException('No Token')
            authorization_str = '{0} {1}'.format(self._store['token_type'], self._store["token"])
            headers['Authorization'] = authorization_str

        return headers

    def get(self, **kwargs):
        try:
            resp = requests.get(self.url(), headers=self._get_header(), params=kwargs, verify=self._store['verify'])
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        return self._process_response(resp)

    def post(self, data=None, **kwargs):
        if data:
            payload = json.dumps(data)
        else:
            payload = None

        try:
            resp = requests.post(
                self.url(), data=payload, headers=self._get_header(), params=kwargs, verify=self._store['verify']
            )
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        return self._process_response(resp)

    def patch(self, data=None, **kwargs):
        if data:
            payload = json.dumps(data)
        else:
            payload = None

        try:
            resp = requests.patch(
                self.url(), data=payload, headers=self._get_header(),params=kwargs,  verify=self._store['verify']
            )
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        return self._process_response(resp)

    def put(self, data=None, **kwargs):
        if data:
            payload = json.dumps(data)
        else:
            payload = None

        try:
            resp = requests.put(
                self.url(), data=payload, headers=self._get_header(), params=kwargs, verify=self._store['verify']
            )
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        return self._process_response(resp)

    def delete(self, data=None, **kwargs):
        if data:
            payload = json.dumps(data)
        else:
            payload = None

        try:
            resp = requests.delete(
                self.url(), headers=self._get_header(), data=payload, params=kwargs, verify=self._store['verify']
            )
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        if 200 <= resp.status_code <= 299:
            if resp.status_code == 204:
                return True
            else:
                return True  # @@@ Should this really be True?
        else:
            return False

    def upload_file(self, filename, mode='rb', **kwargs):
        try:
            payload = {
                'file': open(filename, mode)
            }
        except Exception as e:
            raise RestBaseException(str(e))

        headers = {}
        authorization_str = '{0} {1}'.format(self._store['token_type'], self._store["token"])
        headers['Authorization'] = authorization_str
        logger.debug('Uploading file to {}'.format(str(kwargs)))

        try:
            resp = requests.post(self.url(), files=payload, headers=headers, params=kwargs, verify=self._store['verify'])
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        return self._process_response(resp)

    def _get_resource(self, **kwargs):
        return self.__class__(**kwargs)


class Api(object):
    token = None
    token_type = DEFAULT_TOKEN_TYPE
    domain = DOMAIN_NAME
    resource_class = RestResource

    def __init__(self, domain=None, token_type=None, verify=True):
        if domain:
            self.domain = domain
        self.base_url = '{0}/{1}'.format(self.domain, API_PREFIX)
        self.use_token = True
        if token_type:
            self.token_type = token_type

        self.verify = verify

    def set_token(self, token, token_type=None):
        self.token = token
        if token_type:
            self.token_type = token_type

    def login(self, password, email):
        data = {'email': email, 'password': password}
        url = '{0}/{1}'.format(self.base_url, 'auth/login/')

        payload = json.dumps(data)

        try:
            r = requests.post(url, data=payload, headers=DEFAULT_HEADERS, verify=self.verify)
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        if r.status_code == 200:
            content = json.loads(r.content.decode())
            if self.token_type in content:
                self.token = content[self.token_type]

            self.username = content['username']
            logger.debug('Welcome @{0}'.format(self.username))
            return True
        else:
            logger.error('Login failed: ' + str(r.status_code) + ' ' + r.content.decode())
            return False

    def logout(self):
        url = '{0}/{1}'.format(self.base_url, 'auth/logout/')
        headers = DEFAULT_HEADERS
        headers['Authorization'] = '{0} {1}'.format(self.token_type, self.token)

        try:
            r = requests.post(url, headers=headers, verify=self.verify)
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        if r.status_code == 204:
            logger.debug('Goodbye @{0}'.format(self.username))
            self.username = None
            self.token = None
        else:
            logger.error('Logout failed: ' + str(r.status_code) + ' ' + r.content.decode())

    def refresh_token(self):
        """
        Refresh JWT token
        
        :return: True if token was refreshed. False otherwise 
        """
        assert self.token_type == DEFAULT_TOKEN_TYPE
        url = '{0}/{1}'.format(self.base_url, 'auth/api-jwt-refresh/')

        payload = json.dumps({'token': self.token})

        try:
            r = requests.post(url, data=payload, headers=DEFAULT_HEADERS, verify=self.verify)
        except requests.exceptions.SSLError as err:
            raise HttpCouldNotVerifyServerError("Could not verify the server's SSL certificate", err)

        if r.status_code == 200:
            content = json.loads(r.content.decode())
            if 'token' in content:
                self.token = content['token']

                logger.info('Token refreshed')
                return True

        logger.error('Token refresh failed: ' + str(r.status_code) + ' ' + r.content.decode())
        self.token = None
        return False


    def __getattr__(self, item):
        """
        Instead of raising an attribute error, the undefined attribute will
        return a Resource Instance which can be used to make calls to the
        resource identified by the attribute.
        """

        # Don't allow access to 'private' by convention attributes.
        if item.startswith("_"):
            raise AttributeError(item)

        kwargs = {
            'token': self.token,
            'base_url': self.base_url,
            'use_token': self.use_token,
            'token_type': self.token_type,
            'verify': self.verify
        }
        kwargs.update({'base_url': '{0}/{1}/'.format(kwargs['base_url'], item)})

        return self._get_resource(**kwargs)

    def _get_resource(self, **kwargs):
        return self.resource_class(**kwargs)
