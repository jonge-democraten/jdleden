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

gemeentes = {};

if __name__ == "__main__":
    for d in AFDELINGEN.keys():
        gemeentes[d] = [];
        for r in AFDELINGEN[d]:
            c.execute("""SELECT id FROM postcodes WHERE
                      4pp >= %s AND 4pp <= %s GROUP BY id""", r)
            for id in c.fetchall():
                gemeentes[d].append(id[0]);
            #gemeentes[d] = c.fetchall()
    print json.dumps(gemeentes)
