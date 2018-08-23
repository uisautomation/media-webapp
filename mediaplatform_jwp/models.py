import logging

from django.db import models
from django.utils.functional import cached_property

import mediaplatform.models as mpmodels
from smsjwplatform import jwplatform

LOG = logging.getLogger(__name__)


class Video(models.Model):
    """
    A JWPlatform video resource.

    """

    #: JWPlatform video key
    key = models.CharField(primary_key=True, max_length=64, editable=False)

    #: Corresponding :py:class:`mediaplatform.MediaItem`. Accessible from the
    #: :py:class:`mediaplatform.MediaItem` model via the ``jwp`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    item = models.OneToOneField('mediaplatform.MediaItem', related_name='jwp',
                                on_delete=models.SET_NULL, null=True, editable=False)

    #: The updated timestamp from JWPlatform. Used to determine which items need updating. This is
    #: an integer field rather than a datetime field because JWP uses timestamps and we should
    #: store the same value to make sure we compare apples to apples.
    updated = models.BigIntegerField(help_text='Last updated timestamp', editable=False)

    def get_sources(self):
        """
        Uses the JWP fetch API to retrieve a list of :py:class:`mediaplatform.MediaItem.Source`
        instances for each source associated with the media item. Ignores the ``downloadable``
        attribute of the item.

        """
        try:
            video = jwplatform.DeliveryVideo.from_key(self.key)
        except jwplatform.VideoNotFoundError as e:
            # this can occur if the video is still transcoding - better to set the sources to none
            # than fail completely
            LOG.warning("unable to generate download sources as the JW video is not yet available")
            return []

        return [
            mpmodels.MediaItem.Source(
                mime_type=source.get('type'), url=source.get('file'),
                width=source.get('width'), height=source.get('height'),
                item=self.item,
            )
            for source in video.get('sources', [])
        ]

    #: A property which calls get_sources and caches the result.
    sources = cached_property(get_sources, name='sources')


class Channel(models.Model):
    """
    A JWPlatform channel resource.

    """

    #: JWPlatform channel key
    key = models.CharField(primary_key=True, max_length=64, editable=False)

    #: Corresponding :py:class:`mediaplatform.Channel`. Accessible from the
    #: :py:class:`mediaplatform.Channel` model via the ``jwp`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    channel = models.OneToOneField('mediaplatform.Channel', related_name='jwp',
                                   on_delete=models.SET_NULL, null=True, editable=False)

    #: The updated timestamp from JWPlatform. Used to determine which items need updating. This is
    #: an integer field rather than a datetime field because JWP uses timestamps and we should
    #: store the same value to make sure we compare apples to apples.
    updated = models.BigIntegerField(help_text='Last updated timestamp', editable=False)
