#!/usr/bin/env python

import sys
import os
import csv
import MySQLdb
import xlrd
import time
import hashlib

t = time.strftime("%s")

#DB_NAME = "joomla16"
#DB_USER = "joomla16"
## trick to read keyfile from same dir as actual script, even when called via symlink
#keyfile = os.path.dirname(os.path.realpath(__file__))+"/ledenlijst.key"
#f = open(keyfile, "r")
#DBPASSWD = f.readline().rstrip()
#f.close()
DB_NAME = "jddev"
DB_USER = "jddev"
DB_PASSWD = "eJzbNru5wmJrb7FM"

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
		(8200,8259)],
	"Leiden-Haaglanden":[
		(2160,2799)],
	"Rotterdam":[ 
		(2800,3399), 
		(4200,4549)], 
	"Utrecht":[ 
		(3400,4199), 
		(6700,6799), 
		(7300,7399), 
		(8000,8099), # ex-Zwolle 
		(8160,8199), 
		(8250,8299)], 
	"Brabant":[ 
		(4550,5339), 
		(5400,5799)], 
	"Arnhem-Nijmegen":[ 
		(5340,5399), 
		(5800,5899),
		(6500,6699),
		(6800,6859),
		(6880,7099),
		(7200,7299)],
	"Maastricht":[
		(6000,6499)],
	"Twente":[
		(7100,7199),
		(7400,7699),
		(8100,8199)],
	"Groningen":[
		(7700,7999),
		(9300,9999)],
	"Friesland":[
		(8300,9299)]
}


# read a csv file from disk.
def read_csv(f, header=None):
	# Try to guess the csv file format
	file = open(f)
	dialect = csv.Sniffer().sniff(file.read(4096))
	file.seek(0)
	# Lees de data
	reader = csv.reader(file, dialect)
	grid = [r for r in reader][1:] # Remove first row (header)
	# Maak de leden toegankelijk op lidnummer
	leden = {}
	for r in grid:
		leden[int(r[LIDNUMMER])] = r
	return leden

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
			print "geen voor- of achternaam"
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


def usage():
	print "Usage: %s old.xls new.xls" % (sys.argv[0])

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
			

if __name__ == "__main__":
	if len(sys.argv) != 3:
		usage()
		sys.exit(-1)

	print "Verifying sanity...",
	oldfile = sys.argv[1]
	newfile = sys.argv[2]
	with open(oldfile,"r") as f:
		oldsha = hashlib.sha512(f.read()).hexdigest()
	with open(newfile,"r") as f:
		newsha = hashlib.sha512(f.read()).hexdigest()
	with open("checksum.txt","r") as f:
		# als nog geen checksum, huidige old gebruiken
		storedsha = f.read() or oldsha
	if oldsha == storedsha:
		with open("checksum.txt","w") as f:
			f.write(newsha + "\n")
			print "Sane"
	else:
		print "Wrong old.xls"
		sys.exit(-1)
	print "Reading member lists...",
	old = read_xls(oldfile)
	new = read_xls(newfile)
	print "Done"

	print "Computing changes...",
	plus, min = get_new_and_former_members(old, new)
	changed = get_changed_members(old, new)
	print "Done"

	print "Writing cvs files:"
	plus_split = split_by_department(plus)
	min_split = split_by_department(min)
	changed_split = split_by_department(changed)
	directory = time.strftime("historie.%F")
	os.mkdir(directory, 0700)
	for d in plus_split.keys():
		print "%s-plus.csv\t%d" % (d, len(plus_split[d]))
		write_csv("%s/%s-plus.csv" % (directory,d), plus_split[d])
	for d in min_split.keys():
		print "%s-min.csv\t%d" % (d, len(min_split[d]))
		write_csv("%s/%s-min.csv" % (directory,d), min_split[d])
	for d in changed_split.keys():
		print "%s-upd.csv\t%d" % (d, len(changed_split[d]))
		write_csv("%s/%s-upd.csv" % (directory,d), changed_split[d])

	# XXX weghalen
	sys.exit(0)
	
	# In de jnews tables gebruik ik het email adres als identifier voor de persoon.
	# De lid id kan niet gebruikt worden vanwege mogelijke collisions door 2 
	# onafhankelijke inschrijfmogenlijkheden (nieuwsbrief form en ledenadministratie).
	db = MySQLdb.connect(user=DB_USER, passwd=DB_PASSWD, db=DB_NAME)
	c = db.cursor()
	c.execute("BEGIN")

	# remove old members
	for m in min:
		#print("DELETE FROM j16_jnews_listssubscribers WHERE subscriber_id = (SELECT id FROM j16_jnews_subscribers WHERE 'email' = '%s')"% min[m][EMAIL]).encode("utf-8")
		c.execute("DELETE FROM j16_jnews_listssubscribers WHERE subscriber_id = (SELECT id FROM j16_jnews_subscribers WHERE 'email' = '%s')"% min[m][EMAIL])

	print "Removing complete"
	
	# update changed members
	for id in changed.keys():
		if (changed[id][NAAM] != old[id][NAAM] or changed[id][EMAIL] != old[id][EMAIL]):
			value = (changed[id][NAAM], changed[id][EMAIL], old[id][EMAIL])
			#print("UPDATE IGNORE j16_jnews_subscribers SET name='%s', email='%s' WHERE email='%s'"% value).encode("utf-8")
			c.execute("UPDATE IGNORE j16_jnews_subscribers SET name='%s', email='%s' WHERE email='%s'"% value)
	print "Changes complete"	
	# Add new members	
	for d in plus_split.keys():
		for id in plus_split[d].keys():
			value = (plus_split[d][id][NAAM], plus_split[d][id][EMAIL], 1, t)
			#print("INSERT INTO j16_jnews_subscribers (name, email, confirmed, subscribe_date) VALUES (\"%s\", \"%s\", \"%s\", \"%s\") ON DUPLICATE KEY UPDATE id=id"% value).encode("utf-8")
			c.execute("INSERT INTO j16_jnews_subscribers (name, email, confirmed, subscribe_date) VALUES (\"%s\", \"%s\", \"%s\", \"%s\") ON DUPLICATE KEY UPDATE id=id"% value)
	print "Adding complete"
	c.execute("COMMIT")
#	c.execute("ROLLBACK")
	
	c.execute("BEGIN")
	# Add the new members to their department
	for d in plus_split.keys():
#		values = [(db.escape_string(plus_split[d][id][EMAIL]), db.escape_string("Digizine")) for id in plus_split[d].keys()]
		values = [(db.escape_string(plus_split[d][id][EMAIL]), db.escape_string("Digizine"), db.escape_string("Nieuwsbrief "+d)) for id in plus_split[d].keys()]
		for v in values:
			
			try:
				sql = """INSERT INTO j16_jnews_listssubscribers (subscriber_id, list_id) VALUES ((SELECT id FROM j16_jnews_subscribers WHERE email = \"%s\" LIMIT 1), (SELECT id FROM j16_jnews_lists WHERE list_name = \"%s\")) ON DUPLICATE KEY UPDATE list_id = list_id""" %(v[0],v[1])
				c.execute(sql)
				if v[2] != "Nieuwsbrief Buitenland":
					sql = """INSERT INTO j16_jnews_listssubscribers (subscriber_id, list_id) VALUES ((SELECT id FROM j16_jnews_subscribers WHERE email = \"%s\" LIMIT 1), (SELECT id FROM j16_jnews_lists WHERE list_name = \"%s\")) ON DUPLICATE KEY UPDATE list_id = list_id""" %(v[0],v[2])
				c.execute(sql)
			except:
				print "Error executing \"%s\"" %sql
				c.execute("ROLLBACK")
				db.close()
				sys.exit()
	

	c.execute("COMMIT")
#	c.execute("ROLLBACK")
	print "Added to mailinglists"	


