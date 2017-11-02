"""Tests to ensure that Api() works with unverified remote servers."""

import pytest
import json
from iotile_cloud.api.connection import Api, RestResource
from iotile_cloud.api.exceptions import HttpClientError, HttpServerError, HttpCouldNotVerifyServerError


def test_deny_unverified_by_default(httpsserver):
    """Ensure that we throw an error by default for self-signed servers."""

    api = Api(domain=httpsserver.url)

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.login('test@test.com', 'test')

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.logout()

    with pytest.raises(HttpCouldNotVerifyServerError):
        api.refresh_token()

    # Also ensure that the RestResource works as well
    resource = api.event

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.get()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.put()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.patch()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.post()

    with pytest.raises(HttpCouldNotVerifyServerError):
        resource.delete()


def test_allow_unverified_option(httpsserver):
    """Ensure that we allow unverified servers if the user passes a flag."""

    api = Api(domain=httpsserver.url, verify=False)

    api.login('test@test.com', 'test')
    api.logout()
    api.refresh_token()

    # Also ensure that the RestResource works as well
    resource = api.event

    resource.get()
    resource.put()
    resource.patch()
    resource.post()
    resource.delete()
