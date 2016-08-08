#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

import sys
import os
import errno
import time
import datetime
import hashlib
import configparser
from optparse import OptionParser
from afdelingen import AFDELINGEN
from hemresadapter import HemresAdapter

import xlrd
import xlwt
import ldap
import ldap.modlist as modlist

from jdledenlogger import logger

NOW = time.strftime("%s")          # Epoch-time
NOWHUMAN = time.strftime("%F %T")  # Human-readable time
# Trick to establish the directory of the actual script, even when called
# via symlink.  The purpose of this is to write output-files relative to
# the script-directory, not the current directory.
SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
CHECKSUMFILE = os.path.join(SCRIPTDIR, "checksum.txt")

# Give all important columns a name
LIDNUMMER  = 0
NAAM       = 4
POSTCODE   = 8
WOONPLAATS = 9
LAND       = 11
STEMRECHT  = 17
EMAIL      = 18
GEBDATUM   = 22

# The headers of the input file must exactly match the following definition
HEADERS = [
    u'Relatienummer',
    u'Achternaam', u'Voorletters', u'Tussenvoegsel', u'Volledige naam',
    u'Bez. straat', u'Adres 1: huisnummer', u'Toevoeging',
    u'Postcode (correspondentie adres)', u'Woonplaats (correspondentie adres)',
    u'Gemeente', u'Land (correspondentie adres)',
    u'Geen lid sinds', u'Geen abonnement sinds',
    u'Is lid D66', u'Stemrecht D66', u'Is lid JD', u'Stemrecht JD',
    u'E-mail privé', u'Mobiele telefoon', u'Prive telefoonnummer',
    u'Geslacht', u'Geboortedatum',
    u'Ontbrekende gegevens', u'Vrij tekstveld test',
    u'Aanhef formeel', u'Aanhef informeel',
    u'Betaalmethodevoorkeur',
    u'Overleden'
]

# Excel-output formatting
STYLE_DEFAULT = xlwt.Style.default_style
STYLE_HEADER = xlwt.easyxf("font: bold on")
STYLE_DATE = xlwt.easyxf(num_format_str="YYYY-MM-DD")

# Distinguish between dates and other field types
CELL_STYLES = [
    STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DATE,    STYLE_DATE,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DATE,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT
]

# Every 1000 is 0.3 inch is 7.62 mm (full metal jacket)
COLUMN_WIDTHS = [
    2000,
    3000, 2000, 2000, 5000,
    5000, 2000, 2000,
    2000, 3000,
    3000, 3000,
    3000, 3000,
    2000, 2000, 2000, 2000,
    5000, 3000, 3000,
    2000, 3000,
    1000, 1000,
    1000, 1000,
    1000, 1000
]

# Read configuration-file
config = configparser.RawConfigParser()
config.read(os.path.join(SCRIPTDIR, "ledenlijst.cfg"))
ldapcfg = dict(config.items("ldapcfg"))


class JDldap(object):
    def __init__(self):
        self.ldap_connection = None

    def connect(self):
        self.ldap_connection = ldap.initialize(ldapcfg["name"])
        try:
            self.ldap_connection.simple_bind_s(ldapcfg["dn"], ldapcfg["password"])
        except ldap.LDAPError as e:
            logger.critical(str(e))
            raise

    def disconnect(self):
        self.ldap_connection.unbind_s()

    def doldap_remove(self, id):
        self.check_connection()
        dn_to_delete = "cn=" + str(int(id)) + ",ou=users,dc=jd,dc=nl"
        try:
            self.ldap_connection.delete_s(dn_to_delete)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not remove - " + str(int(id)))
            # raise # this can happen because the database is transactional but the LDAP not yet (script can come here twice)

    def doldap_add(self, lidnummer, naam, mail, afdeling):
        self.check_connection()
        dn_to_add = "cn=" + str(int(lidnummer)) + ",ou=users,dc=jd,dc=nl"
        attrs = {}
        attrs['objectclass'] = ['inetOrgPerson'.encode('utf8')]
        attrs['sn'] = naam.encode('utf8')
        attrs['mail'] = mail.encode('utf8')
        attrs['ou'] = afdeling.encode('utf8')

        ldif = modlist.addModlist(attrs)
        try:
            self.ldap_connection.add_s(dn_to_add, ldif)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not add - " + str(int(lidnummer)))
            # raise # this can happen because the database is transactional but the LDAP not yet (script can come here twice)

    def doldap_modify(self,lidnummer, naam, mail, afdeling):
        self.check_connection()
        dn_to_mod = "cn=" + str(int(lidnummer)) + ",ou=users,dc=jd,dc=nl"
        attrs = [(ldap.MOD_REPLACE, "sn", naam.encode('utf8')), (ldap.MOD_REPLACE, "mail", mail.encode('utf8')),
                 (ldap.MOD_REPLACE, "ou", afdeling.encode('utf8'))]
        try:
            self.ldap_connection.modify_s(dn_to_mod, attrs)
        except ldap.LDAPError as e:
            logger.warning(str(e) + " - Could not modify - " + str(int(lidnummer)))
            raise

    def check_connection(self):
        if not self.ldap_connection:
            raise RuntimeError('No connection with LDAP!')


jdldap = JDldap()


def main():
    # Define command-line options
    usage = """\
    %prog [options] arguments
    in regular mode, arguments is 2 files: old.xls new.xls
    in Excel-only-mode, arguments is 1 file: new.xls"""
    parser = OptionParser(usage)
    parser.add_option("-n", "--dryrun", action="store_true", dest="dryrun", help="don't execute any SQL or LDAP")
    parser.add_option("-x", "--excel", action="store_true", dest="only_excel", help="only generate Excel-files per department")
    # Read options and check sanity
    options, args = parser.parse_args()
    log_script_arguments()

    newfile, oldfile = parse_options(parser, options, args)

    if options.dryrun:
        logger.warning("Dry-run. No LDAP and newsletter changes.")

    logger.info("Reading %s ..." % newfile)
    new = read_xls(newfile)
    logger.info("Reading complete")

    logger.info("Handling department-xls...")
    write_department_excels(new, "uitvoer")
    logger.info("Department-xls complete")

    # Don't run this block in Excel-only-mode
    if not options.only_excel:
        if not options.dryrun:
            jdldap.connect()
        logger.info("Reading %s ..." % oldfile)
        old = read_xls(oldfile)
        logger.info("Reading complete")
        logger.info("Computing changes...")
        new_members, former_members = get_new_and_former_members(old, new)
        changed_members = get_changed_members(old, new)
        current_members_per_dep = split_by_department(new_members)
        logger.info("Computing complete")

        # Remove old members
        logger.info("Removing " + str(len(former_members)) + " members...")
        remove_members_from_ldap(former_members, options.dryrun)
        logger.info("Removing complete.")
        # Update changed members
        logger.info("Updating " + str(len(changed_members)) + " changed members...")
        moved = update_changed_members(old, changed_members, options.dryrun)
        logger.info("Changes complete.")
        # Add new members
        logger.info("Adding " + str(len(new_members)) + " new members...")
        add_members_to_ldap(current_members_per_dep, options.dryrun)
        logger.info("Adding complete.")
        # Add the new members to their department
        logger.info("Subscribing " + str(len(new_members)) + " new members to lists...")
        subscribe_members_to_maillist(current_members_per_dep, options.dryrun)
        logger.info("Subscribing complete.")
        # Unsubscribe moved members from old department and subscribe to new department
        logger.info("Moving " + str(len(moved)) + " members to new departments...")
        moved_split = split_by_department(moved)
        move_members_to_new_department(old, moved_split, options.dryrun)
        write_department_excels(moved, "verhuisd")
        logger.info("Moving complete.")
        logger.info("=== Summary === ")
        logger.info("Removed: " + str(len(former_members)))
        logger.info("Added: " + str(len(new_members)))
        logger.info("Updated: " + str(len(changed_members)))
        logger.info("Changed department: " + str(len(moved)))
        logger.info("==========")
        if not options.dryrun:
            create_new_checksum(newfile)
        logger.info("SUCCESS!")
        if options.dryrun:
            logger.warning("Dry-run. No actual LDAP and Hemres changes!")
        jdldap.disconnect()


def update_changed_members(old, changed, is_dryrun):
    moved = {}
    for id in changed.keys():
        if not is_dryrun:
            jdldap.doldap_modify(changed[id][LIDNUMMER], changed[id][NAAM], changed[id][EMAIL], find_department(parse_postcode(changed[id][POSTCODE])))
        if (changed[id][POSTCODE] != old[id][POSTCODE]):  # Only resubscribe if department actually changes
            newdept = find_department(parse_postcode(changed[id][POSTCODE]))
            olddept = find_department(parse_postcode(old[id][POSTCODE]))
            if (newdept != olddept):
                moved[id] = changed[id]
    return moved


def add_members_to_ldap(plus_split, is_dryrun):
    for d in plus_split.keys():
        for id in plus_split[d].keys():
            if not is_dryrun:
                jdldap.doldap_add(plus_split[d][id][LIDNUMMER], plus_split[d][id][NAAM], plus_split[d][id][EMAIL], d)


def remove_members_from_ldap(members, is_dryrun):
    for id in members:
        if not is_dryrun:
            jdldap.doldap_remove(id)


def subscribe_members_to_maillist(plus_split, is_dryrun):
    hemres = HemresAdapter()
    for d in plus_split.keys():
        for id in plus_split[d].keys():
            if not is_dryrun:
                hemres.subscribe_member_to_list(id, "digizine")
                hemres.subscribe_member_to_list(id, "nieuwsbrief-" + d.lower())


def move_members_to_new_department(old, moved_split, is_dryrun):
    hemres = HemresAdapter()
    for department in moved_split.keys():
        for member_id in moved_split[department].keys():
            newlist = "nieuwsbrief-" + department.lower()
            olddept = find_department(parse_postcode(old[member_id][POSTCODE]))
            oldlist = "nieuwsbrief-" + olddept.lower()
            if not is_dryrun:
                hemres.move_member(member_id, oldlist, newlist)


def parse_options(parser, options, args):
    # Detect which mode we run as and check sanity
    newfile = ""
    oldfile = ""

    if options.only_excel:
        if len(args) != 1:
            parser.error("need 1 argument: new.xls")
        newfile = args[0]
    else:
        if len(args) != 2:
            parser.error("need 2 arguments: old.xls new.xls")
        logger.info("Verifying sanity of input files")
        
        oldfile = args[0]
        newfile = args[1]
        with open(oldfile, "rb") as f:
            hash = hashlib.sha512(f.read())
            oldsha = hash.hexdigest()
        try:
            f = open(CHECKSUMFILE, "r") 
        except IOError as e:
            # If no checksum.txt exists, pretend it was correct
            if e.errno == errno.ENOENT:
                storedsha = oldsha
                logger.warning("No checksum.txt found.")
            else:
                raise
        else:
            storedsha = f.readline().split()[0]  # Read sha512sum-compatible checksum-file

        if oldsha == storedsha:
            logger.info("Input files are sane (checksums match)")
        else:
            logger.critical("Wrong old.xls (according to checksum). Please contact the ICT-team if you are not completely sure what to do.")
            sys.exit(1)

    return newfile, oldfile


def create_new_checksum(newfile):
    logger.info("Creating new checksum.txt...")
    with open(newfile, "rb") as f:
        newsha = hashlib.sha512(f.read()).hexdigest()
    with open(CHECKSUMFILE, "w") as checksumfile:  # Write sha512sum-compatible checksum-file
        checksumfile.write("%s  %s\n" % (newsha, newfile))


def write_department_excels(new, directory_name):
    split = split_by_department(new)
    outdir = os.path.join(directory_name, time.strftime("%F %T"))
    trymkdir(outdir, 0o700)
    for dept in split.keys():
        fileDepartment = os.path.join(outdir, dept + ".xls")
        write_xls(fileDepartment, split[dept])


def read_xls(f):
    # Read xls file from disk
    book = xlrd.open_workbook(f)
    sheet = book.sheet_by_index(0)
    leden = {}
    # Make sure the last value is an integer. There was a time when the last cell was called "Totaal", this should not be the case anymore.
    try:
        int(sheet.cell_value(sheet.nrows-1, 0))
    except ValueError:
        logger.critical("Last row in first column is not an integer. Please contact the ICT-team.")
        sys.exit(1)
    # Confirm first row matches with expectations
    for header_expected, header in zip(HEADERS, sheet.row_values(0)):
        if header_expected != header:
            logger.critical("First row does not match expectations, possible format-change. Please contact the ICT-team if you are not completely sure what to do.")
            sys.exit(1)
    if sheet.nrows not in range(4000,7000):
        logger.critical("Total number of rows very different from hardcoded safeguard. Please contact the ICT-team.")
        sys.exit(1)
    # Store all members in dict by member-number
    for i in range(1,sheet.nrows):
        row = sheet.row(i)
        leden[int(row[LIDNUMMER].value)] = [c.value for c in row]
    # Sanitise data
    for id in leden.keys():
        # Convert member id to int
        leden[id][LIDNUMMER] = int(leden[id][LIDNUMMER])
        # Convert voting right to boolean
        if leden[id][STEMRECHT] == "Ja":
            leden[id][STEMRECHT] = True
        elif leden[id][STEMRECHT] == "Nee":
            leden[id][STEMRECHT] = False
        else:
            logger.warning("stemrecht ongedefinieerd voor lid met id: %d, naam: %s" % (id, leden[id][NAAM]) )
    return leden


def write_xls(f, members):
    book = xlwt.Workbook()
    sheet = book.add_sheet("Leden %s" % NOWHUMAN.split(" ")[0])
    # Column widths
    for i in range(len(COLUMN_WIDTHS)):
        sheet.col(i).width = COLUMN_WIDTHS[i]
    # First row of spreadsheet
    for i in range(len(HEADERS)):
        sheet.write(0, i, HEADERS[i], STYLE_HEADER)
    row = 1  # Row 0 is header
    for id in members.keys():
        for c in range(len(members[id])):
            sheet.write(row, c, members[id][c], CELL_STYLES[c])
        row += 1
    return book.save(f)


def parse_postcode(s):
    try:
        return int(s.strip()[:4])
    except:
        return False  # Unknown format


def get_new_and_former_members(oldlist, newlist):
    old = set(oldlist.keys())
    new = set(newlist.keys())
    new_members = dict([(id, newlist[id]) for id in list(new-old)])
    former_members = dict([(id, oldlist[id]) for id in list(old-new)])
    return (new_members, former_members)


def get_changed_members(oldlist, newlist):
    # Get the members who still exist
    intersect = list(set(oldlist.keys()) & set(newlist.keys()))
    # Find out who has changed
    changed = filter(lambda id: oldlist[id] != newlist[id], intersect)
    return dict([(id, newlist[id]) for id in changed])


def find_department(pc):
    if not pc:
        return "Buitenland"
    for d in AFDELINGEN.keys():
        for r in AFDELINGEN[d]:
            if (pc >= r[0]) and (pc <= r[1]):
                return d
    return "Buitenland"


def split_by_department(members):
    s = dict()
    for id in members.keys():
        if members[id][LAND].upper() != 'NEDERLAND':
            d = 'Buitenland'
        else:
            pc = parse_postcode(members[id][POSTCODE])
            d = find_department(pc)
        if not d in s:
            s[d] = dict()
        s[d][id] = members[id]
    return s


def log_script_arguments():
    commandArguments = "Start script with command: "
    for arg in sys.argv:
        commandArguments += arg + " "
    logger.info(commandArguments)


def trymkdir(dir, perm=0o700):
    # Make directory if needed
    try:
        os.makedirs(dir, perm)
    except IOError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def excel_to_date(xldate):
    # Convert Excel-date (float) to datetime-object
    datetuple = xlrd.xldate_as_tuple(xldate, 0)
    date = datetime.date(*datetuple[:3])
    return date


if __name__ == "__main__":
    main()
