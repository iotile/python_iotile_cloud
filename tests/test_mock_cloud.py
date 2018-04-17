"""Tests for interacting with IOTile.cloud."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os.path
from io import BytesIO
import requests
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


def test_data_stream(water_meter):
    """Make sure we can load and access data."""

    domain, _cloud = water_meter

    api = Api(domain=domain, verify=False)
    api.login('test', 'test@arch-iot.com')

    data = api.data.get(filter='s--0000-0077--0000-0000-0000-00d2--5001')

    assert data['count'] == 11
    first = data['results'][0]
    assert first['project'] == 'p--0000-0077'
    assert first['device'] == 'd--0000-0000-0000-00d2'
    assert first['stream'] == 's--0000-0077--0000-0000-0000-00d2--5001'
    assert first['value'] == 37854.1
    assert first['int_value'] == 100


def test_data_frame(water_meter):
    """Make sure we can load and access data."""

    domain, _cloud = water_meter

    api = Api(domain=domain, verify=False)
    api.login('test', 'test@arch-iot.com')

    data = api.df.get(filter='s--0000-0077--0000-0000-0000-00d2--5001', format='csv')

    lines = data.split('\n')
    assert len(lines) == 12
    
    data = [x.split(',') for x in lines]
    assert data[0] == ['row','int_value','stream_slug']
    assert data[1] == ['2017-04-11T20:37:29.608972Z', '37854.1', 's--0000-0077--0000-0000-0000-00d2--5001']


def test_quick_add_functionality(mock_cloud_private_nossl):
    """Make sure quick add functions work."""

    domain, cloud = mock_cloud_private_nossl
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

    # Make sure quick add streamer works (Issue 28)
    slug = cloud.quick_add_streamer(1, 0, 10)
    resp = api.streamer(slug).get()
    print(resp)
    assert resp['last_id'] == 10


def test_quick_add_device(mock_cloud_private_nossl):
    """Make sure quick_add_device works."""

    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)

    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    res = api.streamer.get()
    assert len(res['results']) == 0

    proj_id, slug = cloud.quick_add_project()
    device_slug15 = cloud.quick_add_device(proj_id, 15, streamers=[10, 15])
    device_slug20 = cloud.quick_add_device(proj_id, 20, streamers=[1])
    device_slug = cloud.quick_add_device(proj_id)

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


def test_list_devices(mock_cloud_private_nossl):
    """Make sure we can list and filter devices."""

    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)
    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    proj_id1, _slug1 = cloud.quick_add_project()
    device_slug1_1 = cloud.quick_add_device(proj_id1, 15)
    device_slug1_2 = cloud.quick_add_device(proj_id1, 20)

    proj_id2, _slug2 = cloud.quick_add_project()
    device_slug2_1 = cloud.quick_add_device(proj_id2)
    device_slug2_2 = cloud.quick_add_device(proj_id2)
    device_slug2_3 = cloud.quick_add_device(proj_id2)

    res = api.device.get()
    assert len(res['results']) == 5

    res = api.device.get(project=proj_id1)
    devs = set([x['slug'] for x in res['results']])
    assert device_slug1_1 in devs and device_slug1_2 in devs and len(devs) == 2

    res = api.device.get(project=proj_id2)
    devs = set([x['slug'] for x in res['results']])
    assert device_slug2_1 in devs and device_slug2_2 in devs and device_slug2_3 in devs and len(devs) == 3


def test_quick_add_fleet(mock_cloud_private_nossl):
    """Make sure we can add, list and filter fleets."""

    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)
    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    proj, _slug = cloud.quick_add_project()
    dev1 = cloud.quick_add_device(proj, 1)
    dev2 = cloud.quick_add_device(proj)
    dev3 = cloud.quick_add_device(proj)
    dev4 = cloud.quick_add_device(proj)
    
    fleet = cloud.quick_add_fleet([1, (dev2, False, False), (dev3, True)], True)
    fleet2 = cloud.quick_add_fleet([dev2])

    # Make sure we can list
    res = api.fleet.get()
    assert len(res['results']) == 2

    # Make sure we can get a single fleet
    fleet_data = api.fleet(fleet).get()
    assert fleet_data == cloud.fleets[fleet]

    # Make sure we can get all fleets containing a device
    res = api.fleet().get(device=dev1)
    assert len(res['results']) == 1
    assert res['results'][0]['slug'] == fleet

    res = api.fleet().get(device=dev4)
    assert len(res['results']) == 0

    res = api.fleet().get(device=dev2)
    assert len(res['results']) == 2

    # Make sure we can get all devices in a fleet
    res = api.fleet(fleet).devices.get()
    assert len(res['results']) == 3


def test_upload_report(mock_cloud_private_nossl):
    """Make sure we can upload data."""

    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)
    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    inpath = os.path.join(os.path.dirname(__file__), 'reports', 'report_100readings_10dev.bin')
    with open(inpath, "rb") as infile:
        data = infile.read()

    timestamp = '{}'.format(cloud._fixed_utc_timestr())
    payload = {'file': BytesIO(data)}

    resource = api.streamer.report

    headers = {}
    authorization_str = '{0} {1}'.format(api.token_type, api.token)
    headers['Authorization'] = authorization_str

    # Make sure there are no reports
    resp = api.streamer.report.get()
    assert len(resp['results']) == 0

    resp = requests.post(resource.url(), files=payload, headers=headers, params={'timestamp': timestamp})
    resp = resource._process_response(resp)
    
    # Verify that the response contains a count record
    assert resp['count'] == 100

    # Verify the streamer record exists
    resp = api.streamer('t--0000-0000-0000-000a--0001').get()
    assert resp['last_id'] == 100
    assert resp['selector'] == 0xABCD

    # Verify the report record exists and that the raw file is saved
    resp = api.streamer.report.get()
    assert len(resp['results']) == 1
    rep_id = resp['results'][0]['id']

    report = api.streamer.report(rep_id).get()
    assert report['id'] == rep_id
    assert cloud.raw_report_files[rep_id] == data

def test_device_patch(mock_cloud_private_nossl):
    """Make sure we can patch device data"""
    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)
    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    proj_id, _slug = cloud.quick_add_project()
    device_slug = cloud.quick_add_device(proj_id, 15)

    assert api.device('d--0000-0000-0000-000f').get()['sg'] == 'water-meter-v1-1-0'
    payload = {
        'sg': 'water-meter-v1-1-1'
    }
    api.device('d--0000-0000-0000-000f').patch(payload)

    assert api.device('d--0000-0000-0000-000f').get()['sg'] == 'water-meter-v1-1-1'

def test_get_sg_dt(mock_cloud_private_nossl):
    domain, cloud = mock_cloud_private_nossl
    api = Api(domain=domain)
    cloud.quick_add_user('test@arch-iot.com', 'test')
    api.login('test', 'test@arch-iot.com')

    sg_slug = cloud.quick_add_sg(slug="test-sg", app_tag=1027)
    dt_slug = cloud.quick_add_dt(slug="test-dt", os_tag=1027)

    assert api.sg(sg_slug).get()['slug'] == "test-sg"
    assert api.dt(dt_slug).get()['slug'] == "test-dt"