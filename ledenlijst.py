#!/usr/bin/env python

import sys
import csv
import MySQLdb

DB_NAME = "jddev"
DB_USER = "jddev"
DB_PASSWD = "eJzbNru5wmJrb7FM"

# Geef alle belangrijke kolommen een naam
LIDNUMMER = 0
EMAIL = 10
POSTCODE = 8
NAAM  = 3

# CSV Header
HEADER = [
	"Lidnummer",		"Lidsoort",			"Lid sinds",	"Lid beeindigd",
	"Volledige naam",	"Geslacht",			"Geboortedatum","Straat",
	"Postcode",			"Plaats",			"Emailadres",	"Afdeling",
	"Regio",			"Telefoonnummer",	"Mobiel",		"Stemrecht"
]


# Alle afdelingen met bijbehorende postcode ranges
AFDELINGEN = {
	"Amsterdam":[
		(1000,2159),
		(8200,8259)],
	"LeidenHaaglanden":[
		(2160,2799)],
	"Rotterdam":[
		(2800,3399),
		(4300,4599)],
	"Utrecht":[
		(3400,4299),
		(6700,6799),
		(6860,6879),
		(7300,7399),
		(8260,8299)],
	"Brabant":[
		(4600,5339),
		(5460,5799)],
	"Nijmegen":[
		(5340,5459),
		(5800,5999),
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
		(8300,9299)],
	"Zwolle":[
		(8000,8099)]
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


def write_csv(f, members):
	w = csv.writer(open(f, "w+"))
	w.writerow(HEADER)
	w.writerows(members.values())


def parse_postcode(s):
	return int(s.strip()[:4])

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
	print "Usage: %s old.csv new.csv" % (sys.argv[0])

def split_by_department(members):
	s = dict()
	for d in AFDELINGEN.keys():
		tmp = dict()
		for id in members.keys():
			pc = parse_postcode(members[id][POSTCODE])
			for r in AFDELINGEN[d]:
				if (pc >= r[0]) and (pc <= r[1]):
					tmp[id] = members[id]
		if tmp:
			s[d] = tmp
	return s



if __name__ == "__main__":
	if len(sys.argv) != 3:
		usage()
		sys.exit(-1)

	print "Reading member lists...",
	old = read_csv(sys.argv[1])
	new = read_csv(sys.argv[2])
	print "Done"

	print "Computing changes...",
	plus, min = get_new_and_former_members(old, new)
	changed = get_changed_members(old, new)
	print "Done"
	
	print "Writing cvs files:"
	plus_split = split_by_department(plus)
	min_split = split_by_department(min)
	changed_split = split_by_department(changed)
	for d in plus_split.keys():
		print "%s-plus.csv" % (d), 
		write_csv("%s-plus.csv" % (d), plus_split[d])
		print "Done"
	for d in min_split.keys():
		print "%s-min.csv" % (d),
		write_csv("%s-min.csv" % (d), min_split[d])
		print "Done"
	for d in changed_split.keys():
		print "%s-upd.csv" % (d),
		write_csv("%s-upd.csv" % (d), changed_split[d])
		print "Done"

	# In de acajoom tables gebruik ik het email adres als identifier voor de persoon.
	# De lid id kan niet gebruikt worden vanwege mogelijke collisions door 2 
	# onafhankelijke inschrijfmogenlijkheden (nieuwsbrief form en ledenadministratie).
	db = MySQLdb.connect(user=DB_USER, passwd=DB_PASSWD, db=DB_NAME)
	c = db.cursor()
	
	for d in plus_split.keys():
		values = [(plus_split[d][id][NAAM], plus_split[d][id][EMAIL]) for id in plus_split[d].keys()]
		c.executemany("INSERT INTO jos_acajoom_subscribers ('name', 'email') VALUES ('%s', '%s')", values)
		print rows	

	


