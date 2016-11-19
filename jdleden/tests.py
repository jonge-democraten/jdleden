import os
import shutil

from django.test import TestCase

import jdleden.ledenlijst
import jdleden.afdelingrondschuif
from jdleden import afdelingen
from jdleden import afdelingenoud


class TestCaseLedenlijst(TestCase):
    oldfile = 'testdata/test_data_a.xls'
    newfile = 'testdata/test_data_b.xls'

    def test_update(self):
        output_dir = 'testoutput'
        output_moved_dir = 'testoutput_moved'
        try:
            result = jdleden.ledenlijst.update(
                self.oldfile, self.newfile,
                dryrun=True, output_dir=output_dir, output_moved_dir=output_moved_dir
            )
            self.assertEqual(len(result['removed']), 1)
            self.assertEqual(len(result['added']), 1)
            self.assertEqual(len(result['updated']), 2)
            self.assertEqual(len(result['changed_department']), 1)
            self.assertTrue(os.path.exists(output_dir))
            self.assertTrue(os.path.exists(output_moved_dir))
        finally:  # always remove the generated output
            shutil.rmtree(output_dir)
            shutil.rmtree(output_moved_dir)

    def test_checksum(self):
        checksum_filename = 'testchecksum.txt'
        jdleden.ledenlijst.create_new_checksum(self.newfile, checksum_filename)
        self.assertTrue(os.path.exists(checksum_filename))
        is_same = jdleden.ledenlijst.check_oldfile(self.newfile, checksum_filename)
        self.assertTrue(is_same)
        is_same = jdleden.ledenlijst.check_oldfile(self.oldfile, checksum_filename)
        self.assertFalse(is_same)
        os.remove(checksum_filename)


class TestCaseChangedDepartments(TestCase):
    members_file = 'testdata/test_data_a.xls'

    def test_change_departments(self):
        moved_members = jdleden.afdelingrondschuif.move_members(self.members_file, dryrun=True)
        self.assertEqual(len(moved_members), 454)


class TestCasePostcodeChecks(TestCase):

    def test_check_postcode_overlap(self):
        has_no_overlap = jdleden.afdelingrondschuif.check_overlap_afdelingen(afdelingen.AFDELINGEN)
        self.assertTrue(has_no_overlap)
        has_no_overlap = jdleden.afdelingrondschuif.check_overlap_afdelingen(afdelingenoud.AFDELINGEN)
        self.assertTrue(has_no_overlap)

    def test_check_postcode_ranges(self):
        correct_ranges = jdleden.afdelingrondschuif.check_postcode_ranges(afdelingen.AFDELINGEN)
        self.assertTrue(correct_ranges)
