import logging

from hemres.management.commands.janeus_unsubscribe import Command as CommandUnsub
from hemres.management.commands.janeus_subscribe import Command as CommandSub

from jdleden import ledenlijst
from jdleden import afdelingen
from jdleden import afdelingenoud

logger = logging.getLogger(__name__)


def move_members(members_file, dryrun):
    logger.info('BEGIN')
    logger.info('file: ' + members_file)
    logger.info('dryrun: ' + str(dryrun))
    afdelingen_new = afdelingen.AFDELINGEN
    afdelingen_oud = afdelingenoud.AFDELINGEN
    
    logger.info("Checking consistency new and old postcode ranges...")
    if not check_postcode_indeling(afdelingen_new):
        logger.error('postcode check for new departments failed')
        raise RuntimeError
    if not check_postcode_indeling(afdelingen_oud):
        logger.error('postcode check for old departments failed')
        raise RuntimeError
    logger.info("Reading %s ..." % members_file)
    members = ledenlijst.read_xls(members_file)
    logger.info("Reading complete")
    logger.info("Calculating reallocated members")
    
    logger.info('Members to be moved:')
    reallocated = get_reallocated_members(members)
    for realloc in reallocated:
        town = realloc[9]
        afdeling_from = find_afdeling( afdelingen_oud, ledenlijst.parse_postcode(realloc[ledenlijst.POSTCODE]))
        afdeling_to   = find_afdeling( afdelingen_new, ledenlijst.parse_postcode(realloc[ledenlijst.POSTCODE]))
        logger.info('Move a member living in ' + town + ' from ' + afdeling_from + ' to ' + afdeling_to)

    logger.info("Doing mass (un)subscribes")
    # Iterate over reallocated.values() and move members
    for member in reallocated:
        olddept = find_afdeling(afdelingenoud.AFDELINGEN, ledenlijst.parse_postcode(member[ledenlijst.POSTCODE]))
        newdept = find_afdeling(afdelingen.AFDELINGEN, ledenlijst.parse_postcode(member[ledenlijst.POSTCODE]))
        oldlist = "nieuwsbrief-" + olddept.lower()
        newlist = "nieuwsbrief-" + newdept.lower()
        if not dryrun:
            CommandUnsub.unsubscribe(member[ledenlijst.LIDNUMMER], oldlist)
            CommandSub.subscribe(member[ledenlijst.LIDNUMMER], newlist)
    if dryrun:
        logger.warning("Dry-run. No actual database changes!")
    logger.info('END')
    return reallocated


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
            ledenlijst.logger.warning('invalid postcode: ' + str(postcode) + ' for member living in ' + member[ledenlijst.WOONPLAATS])
    return reallocated_members
 

def find_afdeling(afdelingsgrenzen, postcode):   
    for afdeling, postcodes in afdelingsgrenzen.items():
        for postcoderange in postcodes:
            if postcode >= postcoderange[0] and postcode <= postcoderange[1]:
                return afdeling
    return 'Afdeling unknown'


def check_postcode_indeling(afdelingen):
    no_overlap = check_overlap_afdelingen(afdelingen)
    correct_ranges = check_postcode_ranges(afdelingen)
    return no_overlap and correct_ranges
    
            
def check_postcode_ranges(afdelingsgrenzen):
    correct_ranges = True
    for _afdeling, postcodes in afdelingsgrenzen.items():
        for postcoderange in postcodes:
            if postcoderange[0] > postcoderange[1]:
                ledenlijst.logger.error('wrong range, lower bound is higher than upper bound: ' + str(postcoderange))
                correct_ranges = False
    return correct_ranges

            
def check_overlap_afdelingen(afdelingsgrenzen):
    overlapping_postcodes = []    
    for i in range(1000, 10000):
        counter = 0
        afdelingen = []
        for afdeling, postcodes in afdelingsgrenzen.items():
            for postcoderange in postcodes:
                if i >= postcoderange[0] and i <= postcoderange[1]:
                    counter += 1
                    afdelingen.append(afdeling)
        if counter > 1:
            overlapping_postcodes.append(i)
            ledenlijst.logger.warning('postcode: ' + str(i) + ' in afdelingen: ' + str(afdelingen))
        if counter == 0:
            ledenlijst.logger.warning('postcode: ' + str(i) + ' heeft geen afdeling')
    if len(overlapping_postcodes) > 0:
        ledenlijst.logger.error('overlapping postcodes: ' + str(len(overlapping_postcodes)))
        return False
    return True
