#!/usr/bin/env python

import sys
import csv


# Geef alle belangrijke kolommen een naam
LIDNUMMER = 0
EMAIL = 10
POSTCODE = 8

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


if __name__ == "__main__":
	if len(sys.argv) != 3:
		usage()
		sys.exit(-1)

	old = read_csv(sys.argv[1])
	new = read_csv(sys.argv[2])

	plus, min = get_new_and_former_members(old, new)
	changed = get_changed_members(old, new)

	# Write the new memnders to file for each departement
	for d in AFDELINGEN.keys():
		tmp = dict()
		for id in plus.keys():
			pc = parse_postcode(plus[id][POSTCODE])
			for r in AFDELINGEN[d]:
				if (pc >= r[0]) and (pc <= r[1]):
					tmp[id] = plus[id]
		if tmp:
			write_csv("%s-plus.csv" % (d), tmp)

	write_csv("plus.csv", plus)
	write_csv("min.csv", min)
	write_csv("upd.csv", changed)


