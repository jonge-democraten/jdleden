from django.core.management.base import BaseCommand

from jdleden.afdelingrondschuif import move_members


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('members_file', nargs=1, type=str)
        parser.add_argument("--dryrun", action="store_true", dest="dryrun", help="don't execute any SQL")

    def handle(self, *args, **options):
        move_members(options['members_file'][0], options['dryrun'])

