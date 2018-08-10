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
``--sync-all`` flag to make sure the database is consistent with all cached resources. Skipping
only video or channel resources is controlled via the ``--skip-video-fetch`` and
``--skip-channel-fetch`` flags.

"""
from django.core.management.base import BaseCommand
from django.db import transaction

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
            help=('Do not re-fetch any resources from JWP, only synchronise database '
                  'objects with cache'))
        parser.add_argument(
            '--skip-video-fetch', action='store_true', dest='skip_video_fetch',
            help='Do not re-fetch videos from JWP, only synchronise database objects with cache')
        parser.add_argument(
            '--skip-channel-fetch', action='store_true', dest='skip_channel_fetch',
            help='Do not re-fetch channels from JWP and synchronise with channels')

    @transaction.atomic
    def handle(self, *args, **options):
        # Create the JWPlatform client
        self.client = jwplatform.get_jwplatform_client()

        # Fetch and cache the video resources
        if not options['skip_video_fetch'] and not options['skip_fetch']:
            self.stdout.write('Caching video resources...')
            models.set_resources(self.fetch_videos(), 'video')

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of cached video resources: {}'.format(
            models.CachedResource.videos.count()
        )))

        if not options['skip_channel_fetch'] and not options['skip_fetch']:
            self.stdout.write('Fetching channels...')
            models.set_resources(self.fetch_channels(), 'channel')

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of cached channel resources: {}'.format(
            models.CachedResource.channels.count()
        )))

        # Synchronise cached resources into main application state
        sync.update_related_models_from_cache(update_all_videos=options['sync_all'])

        # Print out the total number of media items
        self.stdout.write(self.style.SUCCESS('Number of media items: {}'.format(
            mediaplatform.models.MediaItem.objects.count()
        )))

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of channels: {}'.format(
            mediaplatform.models.Channel.objects.count()
        )))

    def fetch_videos(self):
        """
        Returns an iterable of dicts representing all video resources in the JWPlatform database.

        """
        return self._fetch_list(self.client.videos.list, 'videos')

    def fetch_channels(self):
        """
        Returns an iterable of dicts representing all channel resources in the JWPlatform database.

        """
        return self._fetch_list(self.client.channels.list, 'channels')

    def _fetch_list(self, list_callable, results_key):
        """
        Returns an iterable of dicts representing all resources in the JWPlatform database returned
        by a given callable.

        """
        current_offset = 0
        while True:
            # We fetch only manual channels since those are the ones we sync via sms2jwplayer.
            results = list_callable(
                types_filter='manual',
                result_offset=current_offset, result_limit=1000).get(results_key, [])
            current_offset += len(results)

            # Stop when we get no results
            if len(results) == 0:
                break

            # Otherwise, print our out progress
            self.stdout.write(f'... resources fetched so far: {current_offset}')

            # Yield each dict in turn to the caller
            for result in results:
                yield result
