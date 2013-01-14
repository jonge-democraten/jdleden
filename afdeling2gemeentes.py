#!/usr/bin/env python

import sys
import os
import ConfigParser
import json

import MySQLdb

# Trick to establish the directory of the actual script, even when called
# via symlink.  The purpose of this is to write output-files relative to
# the script-directory, not the current directory.
SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))

from afdelingen import AFDELINGEN

# Read configuration-file
config = ConfigParser.RawConfigParser()
config.read(os.path.join(SCRIPTDIR, "gemeenteindeling.cfg"))
dbcfg = dict(config.items("database"))

db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
c = db.cursor()

def findDups(gemeentes, id, excl):
    extra = []
    for afd in gemeentes:
        if afd != excl and id in gemeentes[afd]:
            extra.append(afd)
    return extra

gemeentes = {}
output = {}

if __name__ == "__main__":
    for d in AFDELINGEN.keys():
        gemeentes[d] = []
        for r in AFDELINGEN[d]:
            c.execute("""SELECT postcodes.id, naam,
                      (SELECT min(4pp) FROM postcodes WHERE id=gemeentes.id) as `min`,
                      (SELECT max(4pp) FROM postcodes WHERE id=gemeentes.id) as `max`
                      FROM postcodes LEFT JOIN gemeentes ON gemeentes.id = postcodes.id
                      WHERE 4pp >= %s AND 4pp <= %s GROUP BY postcodes.id""", r)
            for g in c.fetchall():
                #if int(g[2]) >= r[0] and int(g[3]) <= r[1]:
                gemeentes[d].append(g)
    print "Betwiste gemeentes:"
    for afd in gemeentes:
        output[afd] = []
        for gem in gemeentes[afd]:
            extra = findDups(gemeentes, gem, afd)
            if len(extra) > 0:
                sys.stdout.write(' '+gem[1]+' ('+str(gem[2])+'-'+str(gem[3])+'): '+afd)
                for ax in extra:
                    sys.stdout.write(', '+ax)
                print('')
            else:
                output[afd].append(gem[0])
    f = open('afdelingen.json','w')
    f.write(json.dumps(output))
    print 'afdeling.json written.'

