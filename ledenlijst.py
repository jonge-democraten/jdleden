#!/usr/bin/env python

import sys
import os
import errno
import time
import datetime
import hashlib
import logging
import ConfigParser
from optparse import OptionParser
from afdelingen import AFDELINGEN

import MySQLdb
import xlrd
import xlwt
import ldap
import ldap.modlist as modlist

NOW = time.strftime("%s")          # Epoch-time
NOWHUMAN = time.strftime("%F %T")  # Human-readable time
# Trick to establish the directory of the actual script, even when called
# via symlink.  The purpose of this is to write output-files relative to
# the script-directory, not the current directory.
SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))

# Give all important columns a name
LIDNUMMER = 0
LIDSINDS = 2
LIDTOT = 3
NAAM  = 4
GEBDATUM = 6
POSTCODE = 8
EMAIL = 10
REGIO = 12
STEMRECHT = 15
# Aid to detect input-format changes
EXPECTED_INPUT_COLUMNS = 16  # Columns 0 to 15 (incl.)
EXPECTED_HEADERS = ['Lidnummer', 'Lidsoort', 'Lid sinds', 'Lid beeindigd', 'Volledige naam', 'Geslacht', 'Geboortedatum', 'Straat', 'Postcode', 'Plaats', 'Emailadres', 'Afdeling', 'Regio', 'Telefoonnummer', 'Mobiel', 'Stemrecht']
# Extra columns not present in input-format
VOORNAAM = 16
ACHTERNAAM = 17
# If amount or ordering of columns in input-format changes, several
# code changes are needed:
# - change numbers of extra columns
# - change HEADER, CELL_STYLE and COLUMN_WIDTH

# Excel-output formatting
STYLE_DEFAULT = xlwt.Style.default_style
STYLE_HEADER = xlwt.easyxf("font: bold on")
STYLE_DATE = xlwt.easyxf(num_format_str="YYYY-MM-DD")
HEADER = [
    "Lidnummer",        "Lidsoort",         "Lid sinds",        "Lid beeindigd",
    "Volledige naam",   "Geslacht",         "Geboortedatum",    "Straat",
    "Postcode",         "Plaats",           "Emailadres",       "Afdeling",
    "Regio",            "Telefoonnummer",   "Mobiel",           "Stemrecht",
    "Voorna(a)m(en)",   "Achternaam",
]
CELL_STYLE = [
    STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DATE,         STYLE_DATE,
    STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DATE,         STYLE_DEFAULT,
    STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DEFAULT,
    STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DEFAULT,      STYLE_DEFAULT,
    STYLE_DEFAULT,      STYLE_DEFAULT,
]
# Every 1000 is 0.3 inch is 7.62 mm (full metal jacket)
COLUMN_WIDTH = [
    2000,               3000,               3000,               3000,
    6000,               3000,               3000,               6000,
    3000,               5000,               8000,               5000,
    5000,               4000,               4000,               2000,
    4000,               4000,
]

# Read configuration-file
config = ConfigParser.RawConfigParser()
config.read(os.path.join(SCRIPTDIR, "ledenlijst.cfg"))
dbcfg = dict(config.items("database"))
ldapcfg = dict(config.items("ldapcfg"))

# Set up logging to console, debug.log and info.log
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fhd = logging.FileHandler(os.path.join(SCRIPTDIR, "debug.log"))
fhd.setLevel(logging.DEBUG)
fhi = logging.FileHandler(os.path.join(SCRIPTDIR, "info.log"))
fhi.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
fhd.setFormatter(formatter)
fhi.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fhd)
logger.addHandler(fhi)


def main():
  # Define command-line options
  usage = """\
Usage: %prog [options] arguments
  in regular and jNews-only-mode, arguments is 2 files: old.xls new.xls
  in Excel-only-mode, arguments is 1 file: new.xls"""
  parser = OptionParser(usage)
  parser.add_option("-n", "--dryrun", action="store_true", dest="dryrun", help="don't execute any SQL")
  parser.add_option("-j", "--jnews", action="store_true", dest="only_jnews", help="only update jNews-subscriptions")
  parser.add_option("-x", "--excel", action="store_true", dest="only_excel", help="only generate Excel-files per department")
# Read options and check sanity
  options, args = parser.parse_args()
  
  newfile, oldfile = parse_options(parser, options, args)
  
  # This code needs to exist above only_jnews- and only_excel-blocks
  # because it applies to both.
  # When running in regular- or only_jnews-mode, require 2 args and check sanity
  # When running in only_excel-mode, require 1 arg
  logger.info("Reading %s ..." % newfile)
  new = read_xls(newfile)
  logger.info("Reading complete")
  # Don't run this block in jNews-only-mode
  if not options.only_jnews:
    logger.info("Handling department-xls...")
    write_department_excels(new) 
    logger.info("Department-xls complete")
  # Don't run this block in Excel-only-mode
  if not options.only_excel:
    logger.info("Reading %s ..." % oldfile)
    old = read_xls(oldfile)
    logger.info("Reading complete")
    logger.info("Computing changes...")
    new_members, former_members = get_new_and_former_members(old, new)
    changed_members = get_changed_members(old, new)
    current_members_per_dep = split_by_department(new_members)
    logger.info("Computing complete")
    # Use email-address instead of member-id to identify subscriptions.
    # Member-id cannot be used because of risk of collisions from two
    # independent subscription-vectors (webform and D66 administration).
    db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
    c = db.cursor()

    # Make everything transactional so we can rollback on errors
    c.begin()
    
    # Remove old members
    logger.info("Removing members...")
    remove_members(former_members, c, options.dryrun)
    logger.info("Removing complete")
    # Update changed members
    logger.info("Updating changed members...")
    moved = update_changed_members(old, changed_members, c, options.dryrun)
    logger.info("Changes complete")
    # Add new members
    logger.info("Adding new members...")
    add_members_to_database(current_members_per_dep, c, options.dryrun)
    logger.info("Adding complete")
    # Add the new members to their department
    logger.info("Subscribing new members to lists...")
    subscribe_members_to_maillist(current_members_per_dep, db, c, options.dryrun)
    logger.info("Subscribing complete") # Unsubscribe moved members from old department and subscribe to new department
    # FIXME DRY
    logger.info("Moving members to new departments...")
    moved_split = split_by_department(moved)
    move_members_to_new_department(old, db, c, moved_split, options.dryrun)
    logger.info("Moving complete")

    # If we end up here, assume everything is alright
    c.commit()
    

def remove_members(min, c, is_dryrun):
  for m in min:
    value = NOW, min[m][EMAIL]
    sql = "UPDATE IGNORE 2gWw_jnews_listssubscribers SET unsubdate=%s, unsubscribe=1 WHERE subscriber_id = (SELECT id FROM 2gWw_jnews_subscribers WHERE email=%s)"
    dosql(c, sql, value, is_dryrun)
    doldap_remove(m)
    
def update_changed_members(old, changed, c, is_dryrun):
  moved = {}
  for id in changed.keys():
    doldap_modify(changed[id][LIDNUMMER], format_name(changed[id][NAAM], changed[id][VOORNAAM], changed[id][ACHTERNAAM]), changed[id][EMAIL], find_department(parse_postcode(changed[id][POSTCODE]))) 
    if (changed[id][NAAM] != old[id][NAAM] or changed[id][EMAIL] != old[id][EMAIL]):
      name = format_name(changed[id][NAAM], changed[id][VOORNAAM], changed[id][ACHTERNAAM])
      value = name, changed[id][EMAIL], old[id][EMAIL]
      sql = "UPDATE IGNORE 2gWw_jnews_subscribers SET name=%s, email=%s WHERE email=%s"
      dosql(c, sql, value, is_dryrun) # Check if member has moved to a new department
    if (changed[id][POSTCODE] != old[id][POSTCODE]): # Only resubscribe if department actually changes
      newdept = find_department(parse_postcode(changed[id][POSTCODE]))
      olddept = find_department(parse_postcode(old[id][POSTCODE]))
      if (newdept != olddept):
        moved[id] = changed[id]
  return moved

def add_members_to_database(plus_split, c, is_dryrun):
  for d in plus_split.keys():
    for id in plus_split[d].keys():
      name = format_name(plus_split[d][id][NAAM], plus_split[d][id][VOORNAAM], plus_split[d][id][ACHTERNAAM])
      value = name, plus_split[d][id][EMAIL], 1, NOW
      sql = "INSERT INTO 2gWw_jnews_subscribers (name, email, confirmed, subscribe_date) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id"
      dosql(c, sql, value, is_dryrun)
      doldap_add(plus_split[d][id][LIDNUMMER], name, plus_split[d][id][EMAIL], d)
      
def subscribe_members_to_maillist(plus_split, db, c, is_dryrun):
  for d in plus_split.keys():
    values = []
    for id in plus_split[d].keys():
      email = db.escape_string(plus_split[d][id][EMAIL])
      values.append((email, "Digizine", "Nieuwsbrief " + d))
    
    for v in values: # Digizine
      sql, value = prepare_subscribe_query(v[0], v[1])
      dosql(c, sql, value, is_dryrun) # Afdelingsnieuwsbrief
      sql, value = prepare_subscribe_query(v[0], v[2])
      dosql(c, sql, value, is_dryrun)  

def move_members_to_new_department(old, db, c, moved_split, is_dryrun):
  for d in moved_split.keys():
    values = []
    for id in moved_split[d].keys():
      email = db.escape_string(moved_split[d][id][EMAIL])
      values.append((email, "Nieuwsbrief " + d))
    
    for v in values: # Unsubscribe old
      olddept = find_department(parse_postcode(old[id][POSTCODE]))
      oldlist = "Nieuwsbrief " + olddept
      value = NOW, oldlist, v[0]
      sql = "UPDATE IGNORE 2gWw_jnews_listssubscribers SET unsubdate=%s, unsubscribe=1 WHERE list_id IN (SELECT id FROM 2gWw_jnews_lists WHERE list_name=%s) AND subscriber_id = (SELECT id FROM 2gWw_jnews_subscribers WHERE email=%s)"
      dosql(c, sql, value, is_dryrun) # Subscribe new
      sql, value = prepare_subscribe_query(v[0], v[1])
      dosql(c, sql, value, is_dryrun)
    
def parse_options(parser, options, args):
  # Detect which mode we run as and check sanity
  newfile = ""
  oldfile = ""
  
  if options.only_jnews and options.only_excel:
    parser.error("options -j and -x are mutually exclusive")
  elif options.only_excel:
    if len(args) != 1:
      parser.error("need 1 argument: new.xls")
    newfile = args[0]
  else:
    if len(args) != 2:
      parser.error("need 2 arguments: old.xls new.xls")
    logger.info("Verifying sanity of input files")
    csumfile = os.path.join(SCRIPTDIR, "checksum.txt")
    oldfile = args[0]
    newfile = args[1]
    with open(oldfile, "r") as f:
      oldsha = hashlib.sha512(f.read()).hexdigest()
    with open(newfile, "r") as f:
      newsha = hashlib.sha512(f.read()).hexdigest()
    try:
      f = open(csumfile, "r")
    except IOError as e:
      # If no checksum.txt exists, pretend it was correct
      if e.errno == errno.ENOENT:
        logger.warning("Will create new checksum.txt")
        storedsha = oldsha
      else:
        raise
    else:
      storedsha = f.readline().split()[0] # Read sha512sum-compatible checksum-file
    
    if oldsha == storedsha:
      with open(csumfile, "w") as f: # Write sha512sum-compatible checksum-file
        f.write("%s  %s\n" % (newsha, newfile))
      logger.info("Input files are sane")
    else:
      logger.critical("Wrong old.xls")
      sys.exit(1)
      
  return newfile, oldfile

def write_department_excels(new):
  split = split_by_department(new)
  outdir = os.path.join("uitvoer", time.strftime("%F %T"))
  trymkdir(outdir, 0700)
  for dept in split.keys():
    fileDepartment = os.path.join(outdir, dept + ".xls")
    write_xls(fileDepartment, split[dept])
  

def read_xls(f):
    # Read xls file from disk
    book = xlrd.open_workbook(f)
    sheet = book.sheet_by_index(0)
    lastrow = sheet.nrows-1
    leden = {}
    # Confirm first row matches with expectations
    if sheet.row_values(0) != EXPECTED_HEADERS:
        logger.critical("First row does not match expectations, possible format-change")
        sys.exit(1)
    # Confirm last row is a sensible total
    if sheet.cell_value(lastrow, 0) != 'Totaal':
        logger.critical("Last row does not seem to be a Total, possible format-change")
        sys.exit(1)
    # XXX adjust this number if JD grows or shrinks
    if sheet.cell_value(lastrow, 1) not in xrange(4000,6000):
        logger.critical("Number of members in last row very different from hardcoded safeguard")
        sys.exit(1)
    if sheet.nrows not in xrange(4000,6000):
        logger.critical("Total number of rows very different from hardcoded safeguard")
        sys.exit(1)
    # Store all members in dict by member-number
    for i in xrange(1,lastrow):  # Skip header and "Totaal:" row
        row = sheet.row(i)
        if len(row) != EXPECTED_INPUT_COLUMNS:
            # If this happens, consult comment near constants
            logger.critical("Wrong amount of columns in input-data, "\
                    "got %d, expected %d." % (len(row), EXPECTED_INPUT_COLUMNS))
            sys.exit(1)
        leden[int(row[LIDNUMMER].value)] = [c.value for c in row]
    # Sanitise data
    for id in leden.keys():
        # Split firstname and lastname
        try:
            lastname, firstname = leden[id][NAAM].split(', ', 1)
        except ValueError:
            logger.warning("[%d] geen voor- of achternaam" % id)
            leden[id] += ['', '']  # Columns need to exist anyway
        else:
            leden[id] += [firstname, lastname]  # Append to existing list
        # Convert member id to int
        leden[id][LIDNUMMER] = int(leden[id][LIDNUMMER])
        # Convert "member since" to date
        try:
            leden[id][LIDSINDS] = excel_to_date(leden[id][LIDSINDS])
        except ValueError, xlrd.XLDateError:
            logger.warning("[%d] geen lidsinds" % id)
        # Convert "member until" to date
        try:
            leden[id][LIDTOT] = excel_to_date(leden[id][LIDTOT])
        except ValueError, xlrd.XLDateError:
            # lidtot is not important
            logger.debug("[%d] geen lidtot" % id)
        # Convert birthdate to date
        try:
            leden[id][GEBDATUM] = excel_to_date(leden[id][GEBDATUM])
        except ValueError, xlrd.XLDateError:
            logger.warning("[%d] geen geboortedatum" % id)
        # Convert voting right to boolean
        if leden[id][STEMRECHT] == "Ja":
            leden[id][STEMRECHT] = True
        elif leden[id][STEMRECHT] == "Nee":
            leden[id][STEMRECHT] = False
        else:
            logger.warning("[%d] stemrecht ongedefinieerd" % id)
    return leden

def write_xls(f, members):
    book = xlwt.Workbook()
    sheet = book.add_sheet("Leden %s" % NOWHUMAN.split(" ")[0])
    # Column widths
    for i in xrange(len(COLUMN_WIDTH)):
        sheet.col(i).width = COLUMN_WIDTH[i]
    # First row of spreadsheet
    for i in xrange(len(HEADER)):
        sheet.write(0, i, HEADER[i], STYLE_HEADER)
    row = 1  # Row 0 is header
    for id in members.keys():
        for c in xrange(len(members[id])):
            sheet.write(row, c, members[id][c], CELL_STYLE[c])
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
        pc = parse_postcode(members[id][POSTCODE])
        if (members[id][REGIO] == "BUITENLAND"):
            d = "Buitenland"
        else:
            d = find_department(pc)
        if not s.has_key(d):
            s[d] = dict()
        s[d][id] = members[id]
    return s

def dosql(c, sql, value, dryrun=False):
    # Consolidate repeated SQL-code into one function (DRY)
    logger.debug((sql % value).encode("utf-8"))
    if not dryrun:
        try:
            c.execute(sql, value)
        except:
            logger.error("Error executing previous query")
    for msg in c.messages:
        logger.debug(msg)

def trymkdir(dir, perm=0700):
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

def prepare_subscribe_query(email, listname):
    value = (email, listname, NOW)
    sql = "INSERT INTO 2gWw_jnews_listssubscribers (subscriber_id, list_id, subdate) VALUES ((SELECT id FROM 2gWw_jnews_subscribers WHERE email=%s LIMIT 1), (SELECT id FROM 2gWw_jnews_lists WHERE list_name=%s), %s) ON DUPLICATE KEY UPDATE list_id = list_id"
    return sql, value

def format_name(fullname, firstname, lastname):
    # Try to format a sensible name even with incomplete data
    if len(firstname) and len(lastname):
        # Complete data, return parsed name
        return "%s %s" % (firstname, lastname)
    elif len(fullname):
        # Incomplete data, return unparsed name
        return fullname
    else:
        # No data at all, return error
        return "ONBEKENDE_NAAM"

def doldap_remove(id):
    l = ldap.initialize(ldapcfg["name"])
    try:    
        l.simple_bind_s(ldapcfg["dn"], ldapcfg["password"])
    except ldap.LDAPError, e:
        logger.critical(str(e))
    
    dn_to_delete = "cn="+str(int(id))+",ou=users,dc=jd,dc=nl"
    try:
        l.delete_s(dn_to_delete)
    except ldap.LDAPError, e:
        logger.warning(str(e) + " - Could not remove - "+str(int(id)))
    l.unbind_s();

def doldap_add(lidnummer, naam, mail, afdeling):
    l = ldap.initialize(ldapcfg["name"])
    try:
        l.simple_bind_s(ldapcfg["dn"], ldapcfg["password"])
    except ldap.LDAPError, e:
        logger.critical(str(e))

    dn_to_add = "cn="+str(int(lidnummer))+",ou=users,dc=jd,dc=nl"
    attrs = {}
    attrs['objectclass'] = ['inetOrgPerson']
    attrs['sn'] = naam.encode('utf-8')
    attrs['mail'] = mail.encode('utf-8')
    attrs['ou'] = afdeling

    ldif = modlist.addModlist(attrs)
    try:
        l.add_s(dn_to_add, ldif)
    except ldap.LDAPError, e:
        logger.warning(str(e) + " - Could not add - "+str(int(lidnummer)))
    l.unbind_s()

def doldap_modify(lidnummer, naam, mail, afdeling):
    l = ldap.initialize(ldapcfg["name"])
    try:
        l.simple_bind_s(ldapcfg["dn"], ldapcfg["password"])
    except ldap.LDAPError, e:
        logger.critical(str(e))

    dn_to_mod = "cn="+str(int(lidnummer))+",ou=users,dc=jd,dc=nl"

    attrs = [(ldap.MOD_REPLACE, "sn", naam.encode('utf-8')), (ldap.MOD_REPLACE, "mail", mail.encode('utf-8')), (ldap.MOD_REPLACE, "ou", afdeling)]

    try:
        l.modify_s(dn_to_mod, attrs)
    except ldap.LDAPError, e:
        logger.warning(str(e) + " - Could not modify - "+str(int(lidnummer)))
    l.unbind_s()


if __name__ == "__main__":
    main()
