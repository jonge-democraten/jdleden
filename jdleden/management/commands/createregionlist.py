import logging

from django.core.management.base import BaseCommand

from jdleden.regionmaillist import create_region_mail_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates a list of email addresses, one per line, for a list of gemeenten.'

    def add_arguments(self, parser):
        parser.add_argument('--ledenlijst', nargs=1, required=True, help="The input ledenlijst.xls file with member info.")
        parser.add_argument("--gemeenten", nargs='+', required=True, help="A list of gemeenten to get members from, separated by whitespaces.")

    def handle(self, *args, **options):
        logger.info('BEGIN!')
        logger.info('input: ' + options['ledenlijst'][0])
        logger.info('gemeenten: ' + str(options['gemeenten']))
        try:
            maillist_filepath, list_length = create_region_mail_list(options['ledenlijst'][0], options['gemeenten'])
            logger.info('mail list created: ' + maillist_filepath + ' with ' + str(list_length) + ' emails')
            logger.info('SUCCESS!')
        except Exception as error:
            logger.exception(error)
            logger.info('FAILURE!')
            raise
