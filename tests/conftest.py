"""Local pytest fixtures."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os.path
import pytest

@pytest.fixture(scope="module")
def water_meter(mock_cloud):
    """Create mock iotile cloud over https with prepopulated data."""

    domain, cloud = mock_cloud
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')

    cloud.add_data(os.path.join(base, 'data', 'basic_cloud.json'))
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud


@pytest.fixture(scope="module")
def water_meter_http(mock_cloud_nossl):
    """Create mock iotile cloud over http with prepopulated data."""

    domain, cloud = mock_cloud_nossl
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')

    cloud.add_data(os.path.join(base, 'data', 'basic_cloud.json'))
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud
