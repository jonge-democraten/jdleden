from django.core.management.base import BaseCommand

from jdleden.ledenlijst import create_department_excels_from_file


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('members_file', nargs=1, type=str)

    def handle(self, *args, **options):
        create_department_excels_from_file(options['members_file'][0])

