"""
The ``jwpfetch`` management command fetches metadata on videos from JWPlayer via the JWPlatform
management API and caches it in the database as a series of
:py:class:`~mediaplatform_jwp.models.CachedResource` objects.

It is designed to be called periodically without arguments to keep the local cache of the
JWPlatform state in sync with reality.

Note that resources which disappear from JWPlayer are *not* deleted from the database. Rather,
their ``deleted_at`` attribute is set to a non-NULL date and time. The specialised object managers
on :py:class`~mediaplatform_jwp.models.CachedResource` understand this and filter out deleted
objects for you.

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

from mediaplatform_jwp import tasks


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

    def handle(self, *args, **options):
        tasks.synchronise(
            sync_all=options['sync_all'],
            skip_video_fetch=options['skip_video_fetch'] or options['skip_fetch'],
            skip_channel_fetch=options['skip_channel_fetch'] or options['skip_fetch']
        )
