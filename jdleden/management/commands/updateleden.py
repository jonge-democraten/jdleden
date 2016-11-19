from django.core.management.base import BaseCommand

from jdleden.ledenlijst import update


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('oldfile', nargs=1, type=str)
        parser.add_argument('newfile', nargs=1, type=str)
        parser.add_argument("--dryrun", action="store_true", dest="dryrun", help="don't execute any SQL or LDAP")
        parser.add_argument("--excel", action="store_true", dest="only_excel", help="only generate Excel-files per department")

    def handle(self, *args, **options):
        print(options['oldfile'][0])
        print(options['newfile'][0])
        update(options['newfile'][0], options['oldfile'][0], options)
