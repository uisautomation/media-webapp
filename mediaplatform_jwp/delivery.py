"""
Get delivery artefacts from the JWP backend.

"""
import logging

from django.conf import settings

from mediaplatform import models as mpmodels
from smsjwplatform import jwplatform


LOG = logging.getLogger(__name__)


def sources_for_item(item):
    """
    Return a list of :py:class:`mediaplatform.MediaItem.Source` instances for each source
    associated with the media item. Ignores the ``downloadable`` attribute.

    """
    if not hasattr(item, 'jwp'):
        return []

    try:
        video = jwplatform.DeliveryVideo.from_key(item.jwp.key)
    except jwplatform.VideoNotFoundError as e:
        # this can occur if the video is still transcoding - better to set the sources to none
        # than fail completely
        LOG.warning("unable to generate download sources as the JW video is not yet available")
        return []

    return [
        mpmodels.MediaItem.Source(
            mime_type=source.get('type'), url=source.get('file'),
            width=source.get('width'), height=source.get('height')
        )
        for source in video.get('sources', [])
    ]


def embed_url_for_item(item):
    """
    Return a URL with an embed view of a :py:class:`mediaplatform.MediaItem`. Returns ``None`` if
    there is no JWP video associated with the item.
    """
    if not hasattr(item, 'jwp'):
        return None

    return jwplatform.player_embed_url(
        item.jwp.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, format='html'
    )
