#!/usr/bin/env python

from ledenlijst import read_xls, EMAIL

import ConfigParser
from optparse import OptionParser
import MySQLdb

import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))

# Read configuration-file
config = ConfigParser.RawConfigParser()
config.read(os.path.join(SCRIPTDIR, "ledenlijst.cfg"))
dbcfg = dict(config.items("database"))
ldapcfg = dict(config.items("ldapcfg"))


def main():
    usage = """\
    %prog [options] arguments"""
    
    parser = OptionParser(usage)
    # Read options and check sanity
    __options, args = parser.parse_args()

    if len(args) != 1:
        parser.error("need 1 argument: leden.xls")
    allmembersfile = args[0]
    
    members = read_xls(allmembersfile) # members is a dict() with lidnr as key

    db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
    cursor = db.cursor()
    
    for memberid in members:
        print members[memberid][EMAIL]
        value = members[memberid][EMAIL]
        sql = "SELECT id FROM 2gWw_jnews_subscribers WHERE email=%s"
        cursor.execute(sql, value)
        data = cursor.fetchall()
        for row in data :
            print row[0]
  
if __name__ == "__main__":
    main()
    