from django.core.management.base import BaseCommand

from oaipmh.tasks import harvest_all_repositories, harvest_repository


class Command(BaseCommand):
    help = 'Harvest metadata from OAI-PMH repositories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--repository', metavar='ID', type=int, action='append',
            help='Fetch from specified repository id. (May be repeated.)'
        )

        parser.add_argument(
            '--fetch-all-records', action='store_true',
            help='Fetch all records, not just those which have changed since last fetch.'
        )

    def handle(self, repository, fetch_all_records, *args, **options):
        if repository is None:
            harvest_all_repositories(fetch_all_records=fetch_all_records)
        else:
            for repository_id in repository:
                harvest_repository(repository_id, fetch_all_records=fetch_all_records)
