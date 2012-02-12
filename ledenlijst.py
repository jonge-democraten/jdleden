#!/usr/bin/env python

import sys
import os
import errno
import csv
import MySQLdb
import xlrd
import time
import hashlib
import ConfigParser
from optparse import OptionParser
import logging

now = time.strftime("%s")	# epoch-time
nowhuman = time.strftime("%F %T")	# human readable time

# trick to read config from same dir as actual script, even when called via symlink
scriptdir = os.path.dirname(os.path.realpath(__file__))
config = ConfigParser.RawConfigParser()
config.read(os.path.join(scriptdir, "ledenlijst.cfg"))
dbcfg = {}
for o, v in config.items("database"):
	dbcfg[o] = v

# set up logging
logdir = os.path.join(scriptdir, "log", nowhuman)
# make directory if needed
try:
	os.makedirs(logdir, 0700)
except IOError as e:
	if e.errno == errno.EEXIST:
		pass
	else:
		raise
# log to console, debug.log and info.log
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fhd = logging.FileHandler(os.path.join(logdir, "debug.log"))
fhd.setLevel(logging.DEBUG)
fhi = logging.FileHandler(os.path.join(logdir, "info.log"))
fhi.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
fhd.setFormatter(formatter)
fhi.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fhd)
logger.addHandler(fhi)

# Geef alle belangrijke kolommen een naam
LIDNUMMER = 0
EMAIL = 10
POSTCODE = 8
NAAM  = 4
REGIO = 12

# CSV Header
HEADER = [
	"Lidnummer", 		"Lidsoort", 		"Lid sinds", 		"Lid beeindigd",
	"Volledige naam", 	"Geslacht", 		"Geboortedatum",	"Straat",
	"Postcode",			"Plaats",			"Emailadres",		"Afdeling",
	"Regio",			"Telefoonnummer",	"Mobiel",			"Stemrecht"
]

# Alle afdelingen met bijbehorende postcode ranges
AFDELINGEN = {
	"Amsterdam":[
		(1000,2159),
		(8200,8249)],
	"Leiden-Haaglanden":[
		(2160,2799)],
	"Rotterdam":[
		(2800,3399),
		(4200,4549)],
	"Utrecht":[
		(3400,4199),
		(6700,6799),
		(7300,7399),
		(8000,8099),
		(8160,8199),
		(8250,8299)],
	"Brabant":[
		(4550,5339),
		(5400,5799)],
	"Arnhem-Nijmegen":[
		(5340,5399),
		(5800,5899),
		(6500,6699),
		(6800,7299)],
	"Maastricht":[
		(5900,6499)],
	"Twente":[
		(7400,7799),
		(8100,8159)],
	"Groningen":[
		(7800,7999),
		(9300,9999)],
	"Friesland":[
		(8300,9299)]
}


# Read xls file from disk
def read_xls(f):
	book = xlrd.open_workbook(f)
	sheet = book.sheet_by_index(0)
	leden = {}
	for i in xrange(1,sheet.nrows-1): # Skip header and "Totaal:" row
		row = sheet.row(i)
		#print i, int(row[LIDNUMMER].value)
		leden[int(row[LIDNUMMER].value)] = [c.value for c in row]
		try:
			leden[int(row[LIDNUMMER].value)][NAAM] = leden[int(row[LIDNUMMER].value)][NAAM].split(', ')[1]+' '+leden[int(row[LIDNUMMER].value)][NAAM].split(', ')[0]
#			leden[int(row[LIDNUMMER].value)][2] = xlrd.xldate_as_tuple(leden[int(row[LIDNUMMER].value)][2], 0)
#			leden[int(row[LIDNUMMER].value)][3] = xlrd.xldate_as_tuple(leden[int(row[LIDNUMMER].value)][3], 0)
#			leden[int(row[LIDNUMMER].value)][6] = xlrd.xldate_as_tuple(leden[int(row[LIDNUMMER].value)][6], 0)
		except:
			logger.warning("geen voor- of achternaam")
	return leden

def write_csv(f, members):
	w = csv.writer(open(f, "w+"))
	w.writerow(HEADER)
	# Ugly hack to convert all values to latin-1 strings
	w.writerows([[unicode(c).encode('latin-1') for c in r] for r in members.values()])

def parse_postcode(s):
	try:
		return int(s.strip()[:4])
	except:
		return False # Unknown format

def get_new_and_former_members(oldlist, newlist):
	old = set(oldlist.keys())
	new = set(newlist.keys())
	new_members = dict([(id, newlist[id]) for id in list(new-old)])
	former_members = dict([(id, oldlist[id]) for id in list(old-new)])
	return (new_members, former_members)

def get_changed_members(oldlist, newlist):
	# Get the members who still exsist
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

def dosql(c, sql, value):
	# DRY - use one function and don't repeat code
	logger.debug((sql % value).encode("utf-8"))
	if not options.dryrun:
		try:
			c.execute(sql, value)
		except:
			logger.error("Error executing previous query")
	for msg in c.messages:
		logger.debug(msg)


if __name__ == "__main__":
	# define command-line options
	usage = """\
Usage: %prog [options] arguments
  in regular and jNews-only-mode, arguments is 2 files: old.xls new.xls
  in Excel-only-mode, arguments is 1 file: new.xls"""
	parser = OptionParser(usage)
	parser.add_option("-n", "--dryrun", action="store_true", dest="dryrun",
					help="don't execute any SQL")
	parser.add_option("-j", "--jnews", action="store_true", dest="only_jnews",
					help="only update jNews-subscriptions")
	parser.add_option("-x", "--excel", action="store_true", dest="only_excel",
					help="only generate Excel-files per department")
	# read options and check sanity
	(options, args) = parser.parse_args()
	if options.only_jnews and options.only_excel:
			parser.error("options -j and -x are mutually exclusive")
	# when running in only_excel-mode, require 1 arg
	elif options.only_excel:
		if len(args) != 1:
			parser.error("need 1 argument: new.xls")
	# when running in regular- or only_jnews-mode, require 2 args and check sanity
	else:
		if len(args) != 2:
			parser.error("need 2 arguments: old.xls new.xls")
		logger.info("Verifying sanity of input files")
		csumfile = os.path.join(scriptdir, "checksum.txt")
		oldfile = args[0]
		newfile = args[1]
		with open(oldfile,"r") as f:
			oldsha = hashlib.sha512(f.read()).hexdigest()
		with open(newfile,"r") as f:
			newsha = hashlib.sha512(f.read()).hexdigest()
		try:
			f = open(csumfile,"r")
		except IOError as e:
			# als nog geen checksum.txt, doe alsof er oldsha in stond
			if e.errno == errno.ENOENT:
				logger.warning("Will create new checksum.txt")
				storedsha = oldsha
			else:
				raise
		else:
			# read sha512sum-compatible checksum-file
			storedsha = f.readline().split()[0]
		if oldsha == storedsha:
			with open(csumfile,"w") as f:
				# write sha512sum-compatible checksum-file
				f.write("%s  %s\n" % (newsha, newfile))
				logger.info("Input files are sane")
		else:
			logger.critical("Wrong old.xls")
			sys.exit(1)

	# FIXME xlwt code should go somewhere around here (before SQL-code)
	if not options.only_jnews:
		logger.info("placeholder xlwt")

	if not options.only_excel:
		logger.info("Reading member lists...")
		old = read_xls(oldfile)
		new = read_xls(newfile)
		logger.info("Reading complete")

		logger.info("Computing changes...")
		plus, min = get_new_and_former_members(old, new)
		changed = get_changed_members(old, new)
		plus_split = split_by_department(plus)
		logger.info("Computing complete")

		# In de jnews tables gebruik ik het email adres als identifier voor de persoon.
		# De lid id kan niet gebruikt worden vanwege mogelijke collisions door 2
		# onafhankelijke inschrijfmogenlijkheden (nieuwsbrief form en ledenadministratie).
		db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
		c = db.cursor()

		# remove old members
		logger.info("Removing members...")
		for m in min:
			value = (now, min[m][EMAIL])
			sql = "UPDATE IGNORE j16_jnews_listssubscribers SET unsubdate=%s, unsubscribe=1 WHERE subscriber_id = (SELECT id FROM j16_jnews_subscribers WHERE email=%s)"
			dosql(c, sql, value)
		logger.info("Removing complete")

		# update changed members
		logger.info("Updating changed members...")
		moved = {}
		for id in changed.keys():
			if (changed[id][NAAM] != old[id][NAAM] or changed[id][EMAIL] != old[id][EMAIL]):
				value = (changed[id][NAAM], changed[id][EMAIL], old[id][EMAIL])
				sql = "UPDATE IGNORE j16_jnews_subscribers SET name=%s, email=%s WHERE email=%s"
				dosql(c, sql, value)
			# check if member has moved to a new department
			if (changed[id][POSTCODE] != old[id][POSTCODE]):
				# only resubscribe if department actually changes
				newdept = find_department(parse_postcode(changed[id][POSTCODE]))
				olddept = find_department(parse_postcode(old[id][POSTCODE]))
				if (newdept != olddept):
					moved[id] = changed[id]
		moved_split = split_by_department(moved)
		logger.info("Changes complete")

		# Add new members
		logger.info("Adding new members...")
		for d in plus_split.keys():
			for id in plus_split[d].keys():
				value = (plus_split[d][id][NAAM], plus_split[d][id][EMAIL], 1, now)
				sql = "INSERT INTO j16_jnews_subscribers (name, email, confirmed, subscribe_date) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id=id"
				dosql(c, sql, value)
		logger.info("Adding complete")

		# Add the new members to their department
		logger.info("Subscribing new members to lists...")
		for d in plus_split.keys():
	#		values = [(db.escape_string(plus_split[d][id][EMAIL]), db.escape_string("Digizine")) for id in plus_split[d].keys()]
			values = [(db.escape_string(plus_split[d][id][EMAIL]), db.escape_string("Digizine"), db.escape_string("Nieuwsbrief "+d)) for id in plus_split[d].keys()]
			for v in values:
				value = (v[0], v[1])
				sql = "INSERT INTO j16_jnews_listssubscribers (subscriber_id, list_id) VALUES ((SELECT id FROM j16_jnews_subscribers WHERE email=%s LIMIT 1), (SELECT id FROM j16_jnews_lists WHERE list_name=%s)) ON DUPLICATE KEY UPDATE list_id = list_id"
				dosql(c, sql, value)
				if v[2] != "Nieuwsbrief Buitenland":
					value = (v[0], v[2])
					sql = "INSERT INTO j16_jnews_listssubscribers (subscriber_id, list_id) VALUES ((SELECT id FROM j16_jnews_subscribers WHERE email=%s LIMIT 1), (SELECT id FROM j16_jnews_lists WHERE list_name=%s)) ON DUPLICATE KEY UPDATE list_id = list_id"
					dosql(c, sql, value)
		logger.info("Subscribing complete")
		# Unsubscribe moved members from old department and subscribe to new department
		# FIXME DRY
		logger.info("Moving members to new departments...")
		for d in moved_split.keys():
			values = [(db.escape_string(moved_split[d][id][EMAIL]), db.escape_string("Nieuwsbrief "+d)) for id in moved_split[d].keys()]
			for v in values:
				# unsubscribe old
				olddept = find_department(parse_postcode(old[id][POSTCODE]))
				oldlist = "Nieuwsbrief "+olddept
				value = (now, oldlist, v[0])
				sql = "UPDATE IGNORE j16_jnews_listssubscribers SET unsubdate=%s, unsubscribe=1 WHERE list_id IN (SELECT id FROM j16_jnews_lists WHERE list_name=%s) AND subscriber_id = (SELECT id FROM j16_jnews_subscribers WHERE email=%s)"
				dosql(c, sql, value)
				# subscribe new
				if v[1] != "Nieuwsbrief Buitenland":
					value = (v[0], v[1], now)
					sql = "INSERT INTO j16_jnews_listssubscribers (subscriber_id, list_id, subdate) VALUES ((SELECT id FROM j16_jnews_subscribers WHERE email=%s LIMIT 1), (SELECT id FROM j16_jnews_lists WHERE list_name=%s), %s) ON DUPLICATE KEY UPDATE list_id = list_id"
					dosql(c, sql, value)
		logger.info("Moving complete")


