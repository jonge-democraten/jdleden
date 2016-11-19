from django.test import TestCase

from jdleden.ledenlijst import update


class TestCaseLedenlijst(TestCase):
    oldfile = 'testdata/test_data_a.xls'
    newfile = 'testdata/test_data_b.xls'

    def test_update(self):
        result = update(self.oldfile, self.newfile, dryrun=True)
        self.assertEqual(len(result['removed']), 0)
        self.assertEqual(len(result['added']), 0)
        self.assertEqual(len(result['updated']), 1)
        self.assertEqual(len(result['changed_department']), 0)

    # def test_checksum(self):
    #     self.assertTrue(False)
