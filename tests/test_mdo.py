import unittest2 as unittest

from iotile_cloud.utils.mdo import *


class MdoTestCase(unittest.TestCase):

    def test_compute_mdo(self):
        mdo = MdoHelper(m=1, d=1)
        self.assertEqual(mdo.compute(5), 5)
        self.assertEqual(mdo.compute(0), 0)
        self.assertEqual(mdo.compute(-10), -10)

        mdo = MdoHelper(m=3, d=2, o=0.5)
        self.assertEqual(mdo.compute(5), 8.0)
        self.assertEqual(mdo.compute(0), 0.5)
        self.assertEqual(mdo.compute(-10), -14.5)

    def test_reverse_compute_mdo(self):
        mdo = MdoHelper(m=1, d=1)
        self.assertEqual(mdo.compute_reverse(5), 5)
        self.assertEqual(mdo.compute_reverse(0), 0)
        self.assertEqual(mdo.compute_reverse(-10), -10)

        mdo = MdoHelper(m=3, d=2, o=0.5)
        self.assertEqual(mdo.compute_reverse(8.0), 5)
        self.assertEqual(mdo.compute_reverse(0.5), 0)
        self.assertEqual(mdo.compute_reverse(-14.5), -10)
