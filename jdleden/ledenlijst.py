# -*- coding: utf-8 -*-

import logging
import sys
import os
import errno
import time
import hashlib
from unittest.mock import create_autospec

import xlrd
import xlwt

from hemres.management.commands import janeus_subscribe
from hemres.management.commands import janeus_unsubscribe

from jdleden.afdelingen import AFDELINGEN
from jdleden.jdldap import JDldap

logger = logging.getLogger(__name__)

NOW = time.strftime("%s")          # Epoch-time
NOWHUMAN = time.strftime("%F %T")  # Human-readable time

# Give all important columns a name
LIDNUMMER  = 0
NAAM       = 1
POSTCODE   = 8
WOONPLAATS = 9
GEMEENTE   = 10
LAND       = 11
STEMRECHT  = 17
EMAIL      = 18
GEBDATUM   = 22

# The headers of the input file must exactly match the following definition
HEADERS = [
    u'Relatienummer',
    u'Volledige naam',
    u'Adres: Achternaam', u'Adres: Tussenvoegsel', u'Adres: Voorletters',
    u'Adres: Straatnaam', u'Adres: Huisnummer', u'Adres: Hnr Toevoeging',
    u'Adres: Postcode', u'Adres: Woonplaats',
    u'Gemeente', u'Adres: Land',
    u'Geen lid sinds', u'Geen abonnement sinds',
    u'Is lid D66', u'Stemrecht D66', u'Is lid JD', u'Stemrecht JD',
    u'E-mail prive', u'Telefoon: Mobiel', u'Telefoon: Prive',
    u'Geslacht',
    u'Geboortedatum',
    u'Ontbrekende gegevens', u'Vrij tekstveld test',
    u'Aanhef formeel', u'Aanhef informeel',
    u'Betaalmethodevoorkeur', u'Gewijzigd op',
    u'Contact: Bulk-e-mail niet toestaan', u'Overleden'
]

# Excel-output formatting
STYLE_DEFAULT = xlwt.Style.default_style
STYLE_HEADER = xlwt.easyxf("font: bold on")
STYLE_DATE = xlwt.easyxf(num_format_str="YYYY-MM-DD")

# Distinguish between dates and other field types
CELL_STYLES = [
    STYLE_DEFAULT,
    STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DATE,    STYLE_DATE,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT, STYLE_DEFAULT, STYLE_DEFAULT,
    STYLE_DEFAULT,
    STYLE_DATE,
    STYLE_DEFAULT, STYLE_DEFAULT,
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


def update(oldfile, newfile, dryrun=False, no_ldap=False, out_dir='uitvoer', out_moved_dir='verhuisd', checksum_file='checksum.txt'):
    if not dryrun and not check_oldfile(oldfile, checksum_file):
        logger.critical('early return')
        return None

    if dryrun:
        logger.warning("Dry-run. No LDAP and newsletter changes.")

    if no_ldap:
        jdldap = create_autospec(JDldap)  # this is a mock jdldap and does nothing, used for testing
    else:
        jdldap = JDldap()

    logger.info("Reading %s ..." % newfile)
    new = read_xls(newfile)
    logger.info("Reading complete")

    logger.info("Handling department-xls...")
    write_department_excels(new, out_dir)
    logger.info("Department-xls complete")

    if not dryrun:
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
    remove_members_from_ldap(former_members, jdldap, dryrun)
    logger.info("Removing complete.")
    # Update changed members
    logger.info("Updating " + str(len(changed_members)) + " changed members...")
    moved = update_changed_members(old, jdldap, changed_members, dryrun)
    logger.info("Changes complete.")
    # Add new members
    logger.info("Adding " + str(len(new_members)) + " new members...")
    add_members_to_ldap(current_members_per_dep, jdldap, dryrun)
    logger.info("Adding complete.")
    # Add the new members to their department
    logger.info("Subscribing " + str(len(new_members)) + " new members to lists...")
    subscribe_members_to_maillist(current_members_per_dep, dryrun)
    logger.info("Subscribing complete.")
    # Unsubscribe moved members from old department and subscribe to new department
    logger.info("Moving " + str(len(moved)) + " members to new departments...")
    moved_split = split_by_department(moved)
    move_members_to_new_department(old, moved_split, dryrun)
    write_department_excels(moved, out_moved_dir)
    logger.info("Moving complete.")
    logger.info("=== Summary === ")
    logger.info("Removed: " + str(len(former_members)))
    logger.info("Added: " + str(len(new_members)))
    logger.info("Updated: " + str(len(changed_members)))
    logger.info("Changed department: " + str(len(moved)))
    logger.info("==========")
    if not dryrun:
        create_new_checksum(newfile, checksum_file)
    logger.info("SUCCESS!")
    if dryrun:
        logger.warning("Dry-run. No actual LDAP and Hemres changes!")
    if not dryrun:
        jdldap.disconnect()
    return {
        'removed': former_members,
        'added': new_members,
        'updated': changed_members,
        'changed_department': moved
    }


def update_changed_members(old, jdldap, changed, is_dryrun):
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


def add_members_to_ldap(plus_split, jdldap, is_dryrun):
    for d in plus_split.keys():
        for id in plus_split[d].keys():
            if not is_dryrun:
                jdldap.doldap_add(plus_split[d][id][LIDNUMMER], plus_split[d][id][NAAM], plus_split[d][id][EMAIL], d)


def remove_members_from_ldap(members, jdldap, is_dryrun):
    for id in members:
        if not is_dryrun:
            jdldap.doldap_remove(id)


def subscribe_members_to_maillist(plus_split, is_dryrun):
    for d in plus_split.keys():
        for member_id in plus_split[d].keys():
            if not is_dryrun:
                janeus_subscribe.Command.subscribe(member_id, "digizine")
                janeus_subscribe.Command.subscribe(member_id, "nieuwsbrief-" + d.lower())


def move_members_to_new_department(old, moved_split, is_dryrun):
    for department in moved_split.keys():
        for member_id in moved_split[department].keys():
            newlist = "nieuwsbrief-" + department.lower()
            olddept = find_department(parse_postcode(old[member_id][POSTCODE]))
            oldlist = "nieuwsbrief-" + olddept.lower()
            if not is_dryrun:
                janeus_unsubscribe.Command.unsubscribe(member_id, oldlist)
                janeus_subscribe.Command.subscribe(member_id, newlist)


def check_oldfile(oldfile, checksumfile):
    with open(oldfile, "rb") as f:
        hash = hashlib.sha512(f.read())
        oldsha = hash.hexdigest()
    try:
        f = open(checksumfile, "r")
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
        return True
    else:
        logger.critical("Wrong old.xls (according to checksum). Please contact the ICT-team if you are not completely sure what to do.")
        return False


def create_new_checksum(newfile, checksumfile):
    logger.info("Creating new " + checksumfile)
    with open(newfile, "rb") as f:
        newsha = hashlib.sha512(f.read()).hexdigest()
    with open(checksumfile, "w") as outfile:  # Write sha512sum-compatible checksum-file
        outfile.write("%s  %s\n" % (newsha, newfile))


def create_department_excels_from_file(newfile, output_dir='uitvoer'):
    new = read_xls(newfile)
    write_department_excels(new, output_dir)


def write_department_excels(new, directory_name):
    split = split_by_department(new)
    outdir = os.path.join(directory_name, time.strftime("%F %T"))
    trymkdir(outdir, 0o700)
    for dept in split.keys():
        file_department = os.path.join(outdir, dept + ".xls")
        write_xls(file_department, split[dept])


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
            logger.critical("header: " + header + ", expected: " + header_expected)
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


def trymkdir(dir, perm=0o700):
    # Make directory if needed
    try:
        os.makedirs(dir, perm)
    except IOError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
