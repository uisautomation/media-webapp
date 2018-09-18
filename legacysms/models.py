from collections import namedtuple

from django.db import models, connection


class MediaItem(models.Model):
    """
    A media item hosted on the legacy SMS.

    """
    #: SMS media id
    id = models.BigIntegerField(primary_key=True, editable=False, help_text='Legacy SMS media id')

    #: Corresponding :py:class:`mediaplatform.MediaItem`. Accessible from the
    #: :py:class:`mediaplatform.MediaItem` model via the ``sms`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    item = models.OneToOneField(
        'mediaplatform.MediaItem', related_name='sms', editable=False,
        on_delete=models.SET_NULL, null=True)

    #: The last updated at time from the legacy SMS. Used to determine which items need updating.
    #: Some SMS object have this set to NULL, so we should allow it too.
    last_updated_at = models.DateTimeField(
        help_text='Last updated at time from SMS', editable=False, null=True)

    ResultRow = namedtuple('ResultRow', 'day num_hits')

    def fetch_analytics(self):
        """
        A helper method that returns legacy statistics for the media item.

        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT day, num_hits FROM stats.media_stats_by_day WHERE media_id=%s",
                [self.id]
            )
            return [
                MediaItem.ResultRow._make(row)
                for row in cursor.fetchall()
            ]

    def __str__(self):
        return 'Legacy SMS media item {}'.format(self.id)


class Collection(models.Model):
    """
    A collection hosted on the legacy SMS.

    """
    #: SMS collection id
    id = models.BigIntegerField(
        primary_key=True, editable=False, help_text='Legacy SMS collection id')

    #: Corresponding :py:class:`mediaplatform.Channel`. Accessible from the
    #: :py:class:`mediaplatform.Channel` model via the ``sms`` field. This can be NULL if there
    #: is no corresponding channel hosted by the Media Platform.
    channel = models.OneToOneField(
        'mediaplatform.Channel', related_name='sms', on_delete=models.SET_NULL, null=True,
        editable=False)

    #: Every *sms* Collection has exactly one 'shadow' playlist.
    #: Corresponding :py:class:`mediaplatform.Playlist`.
    #: Accessible from the :py:class:`mediaplatform.Playlist` model via the ``sms`` field.
    #: This can be NULL if there is no corresponding playlist hosted by the Media Platform.
    playlist = models.OneToOneField(
        'mediaplatform.Playlist', related_name='sms', on_delete=models.SET_NULL, null=True,
        editable=False)

    #: The last updated at time from the legacy SMS. Used to determine which collections need
    #: updating. Some SMS object have this set to NULL, so we should allow it too.
    last_updated_at = models.DateTimeField(
        help_text='Last updated at time from SMS', editable=False, null=True)

    def __str__(self):
        return 'Legacy SMS collection {}'.format(self.id)
