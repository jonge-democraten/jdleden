#!/usr/bin/env python3.4

from optparse import OptionParser

import MySQLdb

import ledenlijst

import afdelingenoud
import afdelingen


def main():
    # Define command-line options
    usage = """\
Usage: %prog [options] ledenlijst.xls"""
    parser = OptionParser(usage)
    parser.add_option(
            "-n", "--dryrun", action="store_true", dest="dryrun",
            help="don't execute any SQL")
    
    # Read options and check sanity
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Onjuist aantal argumenten.")
    try:
        newfile = args[0]
    except (ValueError, AttributeError):
        parser.error("Fout in een van de argumenten.")
        
    logger = ledenlijst.logger

    afdelingen_new = afdelingen.AFDELINGEN
    afdelingen_oud = afdelingenoud.AFDELINGEN
    
    logger.info("Checking consistency new and old postcode ranges...")
    check_postcode_indeling(afdelingen_new)
    check_postcode_indeling(afdelingen_oud)

    logger.info("Reading %s ..." % (newfile))
    members = ledenlijst.read_xls(newfile)
    logger.info("Reading complete")
    logger.info("Calculating reallocated members")
    
    logger.info('leden die verplaatst gaan worden:')
    reallocated = get_reallocated_members(members)
    for realloc in reallocated:
        logger.info( realloc[9] + ' van ' + find_afdeling( afdelingen_oud, ledenlijst.parse_postcode(realloc[ledenlijst.POSTCODE]) ) + ' naar ' + find_afdeling( afdelingen_new, ledenlijst.parse_postcode(realloc[ledenlijst.POSTCODE]) ) )
    
    logger.info("Connecting to database")
    dbcfg = ledenlijst.dbcfg
    db = MySQLdb.connect(user=dbcfg["user"], passwd=dbcfg["password"], db=dbcfg["name"])
    # Make everything transactional, will rollback in case of exception
    try:
        with db:
            logger.info("Doing mass (un)subscribes")
            c = db.cursor()
            # Iterate over reallocated.values() and perform the moving
            for member in reallocated:
                email = db.escape_string(member[ledenlijst.EMAIL])
                olddept = find_afdeling( afdelingenoud.AFDELINGEN, ledenlijst.parse_postcode(member[ledenlijst.POSTCODE]) )
                oldlist = "Nieuwsbrief " + olddept
                newdept = find_afdeling( afdelingen.AFDELINGEN, ledenlijst.parse_postcode(member[ledenlijst.POSTCODE]) )
                newlist = "Nieuwsbrief " + newdept
                # Subscribe new
                sql, value = ledenlijst.prepare_subscribe_query(email, newlist)
                ledenlijst.dosql(c, sql, value, options.dryrun)
                # Unsubscribe old
                value = (ledenlijst.NOW, oldlist, email)
                sql = "UPDATE IGNORE 2gWw_jnews_listssubscribers SET unsubdate=%s, unsubscribe=1 WHERE list_id IN (SELECT id FROM 2gWw_jnews_lists WHERE list_name=%s) AND subscriber_id = (SELECT id FROM 2gWw_jnews_subscribers WHERE email=%s)"
                ledenlijst.dosql(c, sql, value, options.dryrun)
            if options.dryrun:
                logger.warning("Dry-run. No actual database changes!")
    except:
        logger.error("FAILURE: Problem while trying to execute database query. Transaction is not committed! Nothing has changed in the database.")
        logger.error("Exception:", exc_info=sys.exc_info())
          
def get_reallocated_members(members):
    reallocated_members = []
    for member in members.values():
        postcode_string = member[ledenlijst.POSTCODE]
        postcode = ledenlijst.parse_postcode(postcode_string)
        if not postcode:
            continue
        
        if postcode >= 1000 and postcode < 10000:
            afdeling_old = find_afdeling(afdelingenoud.AFDELINGEN, postcode)
            afdeling_new = find_afdeling(afdelingen.AFDELINGEN, postcode)
            if afdeling_new != afdeling_old:
                reallocated_members.append(member)
        else:
            ledenlijst.logger.warning('invalid postcode: ' + str(postcode))
    
    return reallocated_members
 

def find_afdeling(afdelingsgrenzen, postcode):   
    for afdeling, postcodes in afdelingsgrenzen.items():
        for postcoderange in postcodes:
            if (postcode >= postcoderange[0] and postcode <= postcoderange[1]):
                return afdeling
    return 'Afdeling unknown'


def check_postcode_indeling(afdelingen):
    check_overlap_afdelingen(afdelingen)
    check_postcode_ranges(afdelingen)
    
            
def check_postcode_ranges(afdelingsgrenzen):
    for _afdeling, postcodes in afdelingsgrenzen.items():
        for postcoderange in postcodes:
            if postcoderange[0] > postcoderange[1]:
                ledenlijst.logger.error('wrong range, lower bound is higher than upper bound: ' + str(postcoderange))
                
            
def check_overlap_afdelingen(afdelingsgrenzen):
    overlapping_postcodes = []    
    for i in range(1000, 10000):
        counter = 0
        afdelingen = []
        for afdeling, postcodes in afdelingsgrenzen.items():
            for postcoderange in postcodes:
                if (i >= postcoderange[0] and i <= postcoderange[1]):
                    counter += 1
                    afdelingen.append(afdeling)
        if counter > 1:
            overlapping_postcodes.append(i)
            ledenlijst.logger.warning( 'postcode: ' + str(i) + ' in afdelingen: ' + str(afdelingen) )
        if counter == 0:
            ledenlijst.logger.warning( 'postcode: ' + str(i) + ' heeft geen afdeling' )    
    
    if len(overlapping_postcodes) > 0:
        ledenlijst.logger.error( 'overlapping postcodes: ' + str(len(overlapping_postcodes)) )

        
if __name__ == "__main__":
    main()
