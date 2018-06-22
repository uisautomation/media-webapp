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

"""
from django.core.management.base import BaseCommand

from smsjwplatform import models
from smsjwplatform import jwplatform


class Command(BaseCommand):
    help = 'Fetch metadata from JWPlayer using the management API and cache it in the database.'

    def handle(self, *args, **options):
        # Create the JWPlatform client
        self.client = jwplatform.get_jwplatform_client()

        # Fetch and cache the video resources
        self.stdout.write('Caching video resources...')
        models.CachedResource.videos.set_resources(
            (video['key'], video) for video in self.fetch_videos()
        )

        # Print out the total number of videos cached
        self.stdout.write(self.style.SUCCESS('Number of cached video resources: {}'.format(
            models.CachedResource.videos.count()
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
