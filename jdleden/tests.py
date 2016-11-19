from django.test import TestCase

from jdleden.ledenlijst import update


class TestCaseLedenlijst(TestCase):
    oldfile = 'testdata/test_data_a.xls'
    newfile = 'testdata/test_data_b.xls'

    def test_update(self):
        update(self.oldfile, self.newfile, dryrun=True)

    def test_checksum(self):
        self.assertTrue(False)
