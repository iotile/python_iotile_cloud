import unittest2 as unittest

from iotile_cloud.utils.gid import *


class GIDTestCase(unittest.TestCase):

    def test_project_slug(self):
        id = IOTileProjectSlug(5)
        self.assertEqual(str(id), 'p--0000-0005')

        id = IOTileProjectSlug('p--0000-1234')
        self.assertEqual(str(id), 'p--0000-1234')

        id = IOTileProjectSlug('p--1234')
        self.assertEqual(str(id), 'p--0000-1234')

        id = IOTileProjectSlug('0005')
        self.assertEqual(str(id), 'p--0000-0005')

        self.assertEqual(id.formatted_id(), '0000-0005')

    def test_device_slug(self):
        id = IOTileDeviceSlug(5)
        self.assertEqual(str(id), 'd--0000-0000-0000-0005')
        id = IOTileDeviceSlug(0xa)
        self.assertEqual(str(id), 'd--0000-0000-0000-000a')

        id = IOTileDeviceSlug('d--0000-0000-1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = IOTileDeviceSlug('d--0000-0000-0000-1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = IOTileDeviceSlug('d--1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = IOTileDeviceSlug('0005')
        self.assertEqual(str(id), 'd--0000-0000-0000-0005')

        self.assertEqual(id.formatted_id(), '0000-0000-0000-0005')

    def test_block_slug(self):
        id = IOTileBlockSlug(5)
        self.assertEqual(str(id), 'b--0000-0000-0000-0005')
        id = IOTileBlockSlug(0xa)
        self.assertEqual(str(id), 'b--0000-0000-0000-000a')

        self.assertRaises(AssertionError, IOTileBlockSlug, 'b--0000-0000-1234')

        id = IOTileBlockSlug('b--0001-0000-0000-1234')
        self.assertEqual(str(id), 'b--0001-0000-0000-1234')
        self.assertEqual(id._block, '0001')

        id = IOTileBlockSlug('d--1234', block=3)
        self.assertEqual(str(id), 'b--0003-0000-0000-1234')

        id = IOTileBlockSlug('0005', block=3)
        self.assertEqual(str(id), 'b--0003-0000-0000-0005')
        self.assertEqual(id._block, '0003')

        self.assertEqual(id.get_id(), 5)
        self.assertEqual(id.get_block(), 3)

        self.assertEqual(id.formatted_id(), '0003-0000-0000-0005')

    def test_variable_slug(self):
        self.assertRaises(AssertionError, IOTileVariableSlug, 5)

        id = IOTileVariableSlug(5, IOTileProjectSlug('1234'))
        self.assertEqual(str(id), 'v--0000-1234--0005')
        self.assertEqual(id.formatted_local_id(), '0005')

        id = IOTileVariableSlug('0005', IOTileProjectSlug('1234'))
        self.assertEqual(str(id), 'v--0000-1234--0005')

        id = IOTileVariableSlug('v--0000-1234--0005')
        self.assertEqual(str(id), 'v--0000-1234--0005')

    def test_stream_slug(self):
        self.assertRaises(AssertionError, IOTileStreamSlug, 5)
        self.assertRaises(AssertionError, IOTileStreamSlug, 's--0001')

        id = IOTileStreamSlug('s--0000-0001--0000-0000-0000-0002--0003')
        self.assertEqual(str(id), 's--0000-0001--0000-0000-0000-0002--0003')

        project = IOTileProjectSlug(5)
        device = IOTileDeviceSlug(10)
        variable = IOTileVariableSlug('5001', project)

        id = IOTileStreamSlug()
        id.from_parts(project=project, device=device, variable=variable)
        self.assertEqual(str(id), 's--0000-0005--0000-0000-0000-000a--5001')
        self.assertEqual(id.formatted_id(), '0000-0005--0000-0000-0000-000a--5001')

        parts = id.get_parts()
        self.assertEqual(str(parts['project']), str(project))
        self.assertEqual(str(parts['device']), str(device))
        self.assertEqual(str(parts['variable']), str(variable))

    def test_id_property(self):
        project = IOTileProjectSlug(5)
        self.assertEqual(project.get_id(), 5)
        device = IOTileDeviceSlug(10)
        self.assertEqual(device.get_id(), 10)
        variable = IOTileVariableSlug('5001', project)

        id = IOTileStreamSlug()
        id.from_parts(project=project, device=device, variable=variable)
        self.assertRaises(AssertionError, id.get_id)