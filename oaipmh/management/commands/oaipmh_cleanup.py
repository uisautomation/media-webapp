from django.core.management.base import BaseCommand

from oaipmh.tasks import cleanup


class Command(BaseCommand):
    help = 'Ensure database consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full', action='store_true',
            help='Perform a full cleanup which is likely to touch more objects unnecessarily.'
        )

    def handle(self, full, *args, **options):
        cleanup(full=full)
