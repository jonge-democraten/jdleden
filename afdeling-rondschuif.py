#!/usr/bin/env python

import sys
from optparse import OptionParser

import MySQLdb

import ledenlijst

def get_reallocated_members(members, pc_lo, pc_hi):
    # Return only members in specified postcode range
    reallocated = filter(lambda id:
            pc_lo <= ledenlijst.parse_postcode(members[id][ledenlijst.POSTCODE]) <= pc_hi,
            members)
    return dict([(id, members[id]) for id in reallocated])

if __name__ == "__main__":
    # Define command-line options
    usage = """\
Usage: %prog [options] ledenlijst.xls oude_afdeling postcode_laag postcode_hoog"""
    parser = OptionParser(usage)
    parser.add_option(
            "-n", "--dryrun", action="store_true", dest="dryrun",
            help="don't execute any SQL")
    # Read options and check sanity
    (options, args) = parser.parse_args()
    if len(args) != 4:
        parser.error("Onjuist aantal argumenten.")
    try:
        newfile = args[0]
        olddept = args[1]
        pc_lo = int(args[2])
        pc_hi = int(args[3])
    except ValueError, AttributeError:
        parser.error("Fout in een van de argumenten.")
    else:
        if pc_lo > pc_hi:
            parser.error("Lage postcode hoger dan hoge postcode.")
        if not 1000 <= pc_lo <= 9999 or not 1000 <= pc_hi <= 9999:
            parser.error("Ongeldige postcode.")
    logger = ledenlijst.logger
    logger.info("Reading %s ..." % (newfile))
    members = ledenlijst.read_xls(newfile)
    logger.info("Reading complete")
    logger.info("Calculating reallocated members")
    reallocated = get_reallocated_members(members, pc_lo, pc_hi)
    logger.info("Calculating complete")
    # do unsubscribe magic with olddept and jNews
    for v in reallocated.values():
        print map(lambda n: v[n], [0, 4, 8, 9])  # human-readable debug-output
    logger.info("Connecting to database")
    dbcfg = ledenlijst.dbcfg
    db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
    c = db.cursor()
    #value = "jasper.jongmans@jongedemocraten.nl"
    #sql = "SELECT * FROM j16_jnews_listssubscribers WHERE email=%s"
    #ledenlijst.dosql(c, sql, value, True)
    # iterate over reallocated.values() and perform the moving
