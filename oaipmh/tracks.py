import logging

from django.db import transaction

import mediaplatform.models as mpmodels


LOG = logging.getLogger(__name__)


#: Tags applied to media items created for lecture capture
LECTURE_CAPTURE_TAGS = ['Lecture capture']


@transaction.atomic
def ensure_track_media_item(track):
    # Nothing to do if the track already has a media item or if the associated series has no
    # playlist
    if track.media_item_id is not None:
        return
    if track.matterhorn_record.series is None:
        return
    if track.matterhorn_record.series.playlist_id is None:
        return

    if track.url == '' or track.url is None:
        LOG.error(
            'Skipping track "%s" media item creation because URL is unset',
            track.identifier
        )

    # If the track has a non-empty title, use it. Otherwise, fall back to datestamp.
    if track.matterhorn_record.title.strip() != '':
        title = track.matterhorn_record.title
    else:
        title = f'{track.matterhorn_record.record.datestamp}'

    # Get the destination playlist for the media item
    playlist = track.matterhorn_record.series.playlist

    # Create the media item. We copy the tags so that we don't accidentally create all items with
    # the same tags list object. We make use of initially_fetched_from_url to let the backend fetch
    # the media item for us.
    media_item = mpmodels.MediaItem.objects.create(
        title=title, description=track.matterhorn_record.description, channel=playlist.channel,
        downloadable=False, tags=list(LECTURE_CAPTURE_TAGS), initially_fetched_from_url=track.url,
        published_at=track.matterhorn_record.record.datestamp
    )

    # Set the appropriate permission for the media item
    _set_permission_for_media_item(media_item, track.matterhorn_record.series)

    # Set the track media item
    track.media_item = media_item
    track.save()

    # Add media item to playlist
    playlist.media_items.append(media_item.id)
    playlist.save()

    LOG.info('Created media item "%s" for track "%s"', media_item.id, track.identifier)


def _set_permission_for_media_item(media_item, series):
    """
    Set the permission for a media item based on the defaults in the series.

    """
    permission = media_item.view_permission

    permission.reset()
    permission.is_public = series.view_is_public
    permission.is_signed_in = series.view_is_signed_in
    permission.crsids = series.view_crsids
    permission.lookup_groups = series.view_lookup_groups
    permission.lookup_insts = series.view_lookup_insts
    permission.save()
