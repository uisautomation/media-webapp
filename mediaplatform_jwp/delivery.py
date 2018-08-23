"""
Get delivery artefacts from the JWP backend.

"""
import logging

from django.conf import settings

from smsjwplatform import jwplatform


LOG = logging.getLogger(__name__)


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
