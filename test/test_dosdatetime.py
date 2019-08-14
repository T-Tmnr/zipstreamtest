from unittest import TestCase
from dosdatetime import to_dos_datetime, from_dos_datetime
from datetime import datetime


class Test_dosdatetime(TestCase):

    def test_zip_sample_case(self):
        comp = from_dos_datetime(0x2d7a, 0x5ea8)
        expect = datetime(2002, 11, 26, 11, 53, 16)
        self.assertEqual(comp,expect)

        d, t = to_dos_datetime(expect)
        self.assertEqual((d, t), (0x2d7a, 0x5ea8))
