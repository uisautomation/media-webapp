"""
Celery tasks.

"""
import logging

from celery import shared_task
from django.db import transaction

from mediaplatform_jwp import models
from mediaplatform_jwp import sync
from mediaplatform_jwp.api import delivery as jwplatform
import mediaplatform.models


LOG = logging.getLogger(__name__)


@shared_task(name='mediaplatform_jwp.synchronise')
@transaction.atomic
def synchronise(sync_all=False, skip_video_fetch=False, skip_channel_fetch=False):
    """
    Synchronise the list of Cached JWP resources in the database with the actual list of resources
    using the JWP management API.

    For JWP videos which come from the SMS, media items are automatically created as videos apear.

    All JWP videos with corresponding media items have basic metadata such as title and description
    synchronised.

    If *sync_all* is True, all media items are re-synchronised from their corresponding cached JWP
    resource. If False, only those items whose JWP resources have changed are synchronised.

    If *skip_video_fetch* is True, the cached video resources are not re-fetched from JWP.

    If *skip_channel_fetch* is True, the cached channel resources are not re-fetched from JWP.

    """
    # Create the JWPlatform client
    client = jwplatform.get_jwplatform_client()

    # Fetch and cache the video resources
    if not skip_video_fetch:
        LOG.info('Caching video resources...')
        models.set_resources(fetch_videos(client), 'video')

    # Print out the total number of videos cached
    LOG.info('Number of cached video resources: {}'.format(
        models.CachedResource.videos.count()
    ))

    if not skip_channel_fetch:
        LOG.info('Fetching channels...')
        models.set_resources(fetch_channels(client), 'channel')

    # Print out the total number of channels cached
    LOG.info('Number of cached channel resources: {}'.format(
        models.CachedResource.channels.count()
    ))

    # Synchronise cached resources into main application state
    sync.update_related_models_from_cache(update_all_videos=sync_all)

    # Print out the total number of media items
    LOG.info('Number of media items: {}'.format(
        mediaplatform.models.MediaItem.objects.count()
    ))

    # Print out the total number of channels
    LOG.info('Number of channels: {}'.format(
        mediaplatform.models.Channel.objects.count()
    ))


def fetch_videos(client):
    """
    Returns an iterable of dicts representing all video resources in the JWPlatform database.

    """
    return _fetch_list(client.videos.list, 'videos')


def fetch_channels(client):
    """
    Returns an iterable of dicts representing all channel resources in the JWPlatform database.

    """
    return _fetch_list(client.channels.list, 'channels')


def _fetch_list(list_callable, results_key):
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
        LOG.info(f'... resources fetched so far: {current_offset}')

        # Yield each dict in turn to the caller
        for result in results:
            yield result
