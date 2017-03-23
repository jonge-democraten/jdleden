import os
import shutil

from django.test import TestCase

import jdleden.ledenlijst
import jdleden.afdelingrondschuif
from jdleden import afdelingen
from jdleden import afdelingenoud
from jdleden.regionmaillist import create_region_mail_list
from testdata import test_afdelingen


class TestCaseLedenlijst(TestCase):
    oldfile = 'testdata/test_data_a.xls'
    newfile = 'testdata/test_data_b.xls'
    checksum_filename = 'testchecksum.txt'

    def test_update(self):
        output_dir = 'testoutput'
        output_moved_dir = 'testoutput_moved'
        try:
            result = jdleden.ledenlijst.update(
                self.oldfile,
                self.newfile,
                dryrun=False,
                no_ldap=True,
                out_dir=output_dir,
                out_moved_dir=output_moved_dir,
                checksum_file=self.checksum_filename
            )
            self.assertTrue(result is not None)
            self.assertEqual(len(result['removed']), 1)
            self.assertEqual(len(result['added']), 1)
            self.assertEqual(len(result['updated']), 2)
            self.assertEqual(len(result['changed_department']), 1)
            self.assertTrue(os.path.exists(output_dir))
            self.assertTrue(os.path.exists(output_moved_dir))
        finally:  # always remove the generated output
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            if os.path.exists(output_moved_dir):
                shutil.rmtree(output_moved_dir)
            os.remove(self.checksum_filename)

    def test_checksum(self):
        jdleden.ledenlijst.create_new_checksum(self.newfile, self.checksum_filename)
        self.assertTrue(os.path.exists(self.checksum_filename))
        is_same = jdleden.ledenlijst.check_oldfile(self.newfile, self.checksum_filename)
        self.assertTrue(is_same)
        is_same = jdleden.ledenlijst.check_oldfile(self.oldfile, self.checksum_filename)
        self.assertFalse(is_same)
        os.remove(self.checksum_filename)


class TestCaseChangedDepartments(TestCase):
    members_file = 'testdata/test_data_a.xls'

    def test_check_postcodes(self):
        self.assertTrue(jdleden.afdelingrondschuif.check_postcode_indeling(afdelingen.AFDELINGEN))
        self.assertTrue(jdleden.afdelingrondschuif.check_postcode_indeling(afdelingenoud.AFDELINGEN))
        self.assertFalse(jdleden.afdelingrondschuif.check_postcode_indeling(test_afdelingen.AFDELINGEN))
        self.assertFalse(jdleden.afdelingrondschuif.check_overlap_afdelingen(test_afdelingen.AFDELINGEN))
        self.assertFalse(jdleden.afdelingrondschuif.check_postcode_ranges(test_afdelingen.AFDELINGEN))

    def test_change_departments(self):
        moved_members = jdleden.afdelingrondschuif.move_members(self.members_file, dryrun=True)
        self.assertEqual(len(moved_members), 3)  # this needs to be updated after afdelingen and afdelingenoud has changed


class TestCasePostcodeChecks(TestCase):

    def test_check_postcode_overlap(self):
        has_no_overlap = jdleden.afdelingrondschuif.check_overlap_afdelingen(afdelingen.AFDELINGEN)
        self.assertTrue(has_no_overlap)
        has_no_overlap = jdleden.afdelingrondschuif.check_overlap_afdelingen(afdelingenoud.AFDELINGEN)
        self.assertTrue(has_no_overlap)

    def test_check_postcode_ranges(self):
        correct_ranges = jdleden.afdelingrondschuif.check_postcode_ranges(afdelingen.AFDELINGEN)
        self.assertTrue(correct_ranges)


class TestCaseRegionMailList(TestCase):
    members_file = 'testdata/test_data_a.xls'

    def test_create_list_amsterdam(self):
        maillist_filepath, list_length = create_region_mail_list(self.members_file, ['Amsterdam'])
        self.assertTrue(os.path.exists(maillist_filepath))
        self.assertEqual(list_length, 976)
        os.remove(maillist_filepath)
        maillist_filepath, list_length = create_region_mail_list(self.members_file, ['AMSTERDAM'])
        self.assertTrue(os.path.exists(maillist_filepath))
        self.assertEqual(list_length, 976)
        os.remove(maillist_filepath)

    def test_create_list_amsterdam_utrecht(self):
        maillist_filepath, list_length = create_region_mail_list(self.members_file, ['Amsterdam', 'Utrecht'])
        self.assertTrue(os.path.exists(maillist_filepath))
        self.assertEqual(list_length, 1918)
        os.remove(maillist_filepath)

    def test_create_list_haarlem(self):
        maillist_filepath, list_length = create_region_mail_list(self.members_file, ['Haarlem'])
        self.assertTrue(os.path.exists(maillist_filepath))
        self.assertEqual(list_length, 0)
        os.remove(maillist_filepath)
