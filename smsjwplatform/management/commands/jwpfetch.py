"""
The ``jwpfetch`` management command fetches metadata on videos from JWPlayer via the JWPlatform
management API and caches it in the database as a series of
:py:class:`~smsjwplatform.models.CachedResource` objects.

It is designed to be called periodically without arguments to keep the local cache of the
JWPlatform state in sync with reality.

Note that resources which disappear from JWPlayer are *not* deleted from the database. Rather,
their ``deleted_at`` attribute is set to a non-NULL date and time. The specialised object managers
on :py:class`~smsjwplatform.models.CachedResource` understand this and filter out deleted objects
for you.

The ``--sync-all`` flag may be given to bypass the freshness check for updating database objects
from the associated JWP metadata. If given, *all* py:class`mediaplatform.models.MediaItem` objects
associated with a JWP video will have their metadata re-synchronised. This is a useful thing to do
from time to time to make sure that all videos are in sync.

The ``--skip-fetch`` flag may be given to skip updating the cached resources from JWP and to only
perform the database metadata synchronisation. This can be useful in combination with the
``--sync-all`` flag to make sure the database is consistent with all cached resources.

"""
from django.core.management.base import BaseCommand

from smsjwplatform import models
from smsjwplatform import jwplatform
from mediaplatform_jwp import sync
import mediaplatform.models


class Command(BaseCommand):
    help = 'Fetch metadata from JWPlayer using the management API and cache it in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-all', action='store_true', dest='sync_all',
            help='Synchronise all objects from JWP cache, not only those which have been updated')
        parser.add_argument(
            '--skip-fetch', action='store_true', dest='skip_fetch',
            help='Do not re-fetch objects from JWP, only synchronise database objects with cache')

    def handle(self, *args, **options):
        # Create the JWPlatform client
        self.client = jwplatform.get_jwplatform_client()

        # Fetch and cache the video resources
        if not options['skip_fetch']:
            self.stdout.write('Caching video resources...')
            models.set_videos(self.fetch_videos())

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of cached video resources: {}'.format(
            models.CachedResource.videos.count()
        )))

        # Synchronise cached resources into main application state
        sync.update_related_models_from_cache(options['sync_all'])

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of media items: {}'.format(
            mediaplatform.models.MediaItem.objects.count()
        )))

    def fetch_videos(self):
        """
        Returns an iterable of dicts representing all video resources in the JWPlatform database.

        """
        current_offset = 0
        while True:
            results = self.client.videos.list(
                result_offset=current_offset, result_limit=1000).get('videos', [])
            current_offset += len(results)

            # Stop when we get no results
            if len(results) == 0:
                break

            # Otherwise, print our out progress
            self.stdout.write(f'... resources fetched so far: {current_offset}')

            # Yield each dict in turn to the caller
            for result in results:
                yield result
