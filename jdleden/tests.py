import os

from django.test import TestCase

import jdleden.ledenlijst


class TestCaseLedenlijst(TestCase):
    oldfile = 'testdata/test_data_a.xls'
    newfile = 'testdata/test_data_b.xls'

    def test_update(self):
        result = jdleden.ledenlijst.update(self.oldfile, self.newfile, dryrun=True)
        self.assertEqual(len(result['removed']), 1)
        self.assertEqual(len(result['added']), 1)
        self.assertEqual(len(result['updated']), 2)
        self.assertEqual(len(result['changed_department']), 1)

    def test_checksum(self):
        checksum_filename = 'testchecksum.txt'
        jdleden.ledenlijst.create_new_checksum(self.newfile, checksum_filename)
        self.assertTrue(os.path.exists(checksum_filename))
        is_same = jdleden.ledenlijst.check_oldfile(self.newfile, checksum_filename)
        self.assertTrue(is_same)
        is_same = jdleden.ledenlijst.check_oldfile(self.oldfile, checksum_filename)
        self.assertFalse(is_same)
        os.remove(checksum_filename)
