from django.core.management.base import BaseCommand

from jdleden.ledenlijst import update


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('oldfile', nargs=1, type=str)
        parser.add_argument('newfile', nargs=1, type=str)
        parser.add_argument("--dryrun", action="store_true", dest="dryrun", help="don't execute any SQL or LDAP")

    def handle(self, *args, **options):
        update(options['oldfile'][0], options['newfile'][0], dryrun=options['dryrun'])
