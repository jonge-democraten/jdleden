#!/usr/bin/env python

import sys
import csv


# Geef alle belangrijke kolommen een naam
LIDNUMMER = 0
EMAIL = 1

# CSV Header
HEADER = ["Lidnummer", ]


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
def read_csv(f):
	# Try to guess the csv file format
	file = open(f)
	dialect = csv.Sniffer().sniff(file.read(4096))
	file.seek(0)
	# Check for header
	has_header = csv.Sniffer().has_header(file.read(4096))
	file.seek(0)
	# Lees de data
	reader = csv.reader(file, dialect)
	grid = [r for r in reader]
	if has_header:
		grid =  grid[1:]
	# Maak de leden toegankelijk op lidnummer
	leden = {}
	for r in grid:
		leden[int(r[LIDNUMMER])] = r
	return leden


def parse_postcode(s):
	return int(s.strip()[:4])

def get_new_and_former_members(oldlist, newlist):
	old = set(oldlist.keys())
	new = set(newlist.keys())
	new_members = list(new-old)
	former_members = list(old-new)
	return (new_members, former_members)

def get_changed_members(oldlist, newlist):
	# Get the members who still exsist
	same = list(set(oldlist.keys()) or set(newlist.keys()))
	# Find out who has changed
	changed = []
	for id in same:
		if oldlist[id] != newlist[id]
		changed.append(id)
	return changed


def usage():
	print "Usage: %s old.csv new.csv" % (sys.argv[0])


if __name__ == "__main__":
	if len(sys.argv) != 3:
		usage()
		sys.exit(-1)





