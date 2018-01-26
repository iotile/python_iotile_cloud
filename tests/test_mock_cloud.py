"""Tests for interacting with IOTile.cloud."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os.path
import pytest
from iotile_cloud.api.connection import Api
from iotile_cloud.api.exceptions import HttpNotFoundError


def test_mock_cloud_login(water_meter):
    """Make sure the mock cloud is working."""

    domain, cloud = water_meter
    api = Api(domain=domain, verify=False)

    res = api.login('test', 'test@arch-iot.com')
    assert res

    acc = api.account.get()
    print(acc)
    assert len(acc['results']) == 1
    assert acc['results'][0] == {
        "id": 1,
        "email": "unknown email",
        "username": "unknown username",
        "name": "unknown name",
        "slug": "unknown slug"
    }

    res = api.login('test2', 'test@arch-iot.com')
    assert not res

    res = api.login('test', 'test@arch-iot.com1')
    assert not res


def test_http_support(water_meter_http):
    """Make sure we can use the cloud over http as well."""

    domain, cloud = water_meter_http
    api = Api(domain=domain, verify=False)

    res = api.login('test', 'test@arch-iot.com')
    assert res


def test_data_access(water_meter):
    """Make sure we can load and access data."""

    domain, _cloud = water_meter

    api = Api(domain=domain, verify=False)
    api.login('test', 'test@arch-iot.com')

    data = api.device('d--0000-0000-0000-00d2').get()
    assert data['slug'] == 'd--0000-0000-0000-00d2'

    data = api.datablock('b--0001-0000-0000-04e7').get()
    assert data['slug'] == 'b--0001-0000-0000-04e7'

    stream = api.stream('s--0000-0077--0000-0000-0000-00d2--5002').get()
    assert stream['slug'] == 's--0000-0077--0000-0000-0000-00d2--5002'

    proj = api.project('1c07fdd0-3fad-4549-bd56-5af2aca18d5b').get()
    assert proj['slug'] == 'p--0000-0077'

    events = api.event.get(filter="s--0000-0077--0000-0000-0000-00d2--5001")
    res = events['results']
    assert len(res) == 3

    raw1 = api.event(1).data.get()
    assert raw1 == {"test": 1, "hello": 2}

    raw2 = api.event(2).data.get()
    assert raw2 == {"test": 1, "goodbye": 15}

    api.vartype('water-meter-volume').get()


def test_quick_add_functionality(mock_cloud_private):
    """Make sure quick add functions work."""

    domain, cloud = mock_cloud_private
    api = Api(domain=domain)

    res = api.login('test', 'test@arch-iot.com')
    assert res is False

    cloud.quick_add_user('test@arch-iot.com', 'test')
    res = api.login('test', 'test@arch-iot.com')
    assert res is True


    proj_id, slug = cloud.quick_add_project()

    proj_data = api.project(proj_id).get()
    assert proj_data['id'] == proj_id
    assert proj_data['slug'] == slug

    org_data = api.org(proj_data['org']).get()
    assert org_data['slug'] == "quick-test-org"


def test_quick_add_device(mock_cloud_private):
    """Make sure quick_add_device works."""

    domain, cloud = mock_cloud_private
    api = Api(domain=domain)

    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    res = api.streamer.get()
    assert len(res['results']) == 0

    proj_id, slug = cloud.quick_add_project()
    device_slug15 = cloud.quick_add_device(proj_id, 15, streamers=[10, 15])
    device_slug20 = cloud.quick_add_device(proj_id, 20, streamers=[1])

    res = api.streamer.get()
    assert len(res['results']) == 3

    res = api.streamer.get(device=device_slug15)
    assert len(res['results']) == 2

    res = api.streamer('t--0000-0000-0000-000f--0001').get()
    assert res['last_id'] == 15
    assert res['device'] == device_slug15
    assert res['is_system'] is True

    with pytest.raises(HttpNotFoundError):
        api.streamer('t--0000-0000-0000-0015--0001').get()

    res = api.device(device_slug15).get()
    assert res['slug'] == device_slug15

    res = api.device(device_slug20).get()
    assert res['slug'] == device_slug20