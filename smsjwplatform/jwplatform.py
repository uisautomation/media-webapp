"""
Interaction with the JWPlatform API.

"""
import hashlib
import time
import urllib.parse

from django.conf import settings
import jwplatform


class VideoNotFoundError(RuntimeError):
    """
    The provided SMS media ID does not have a corresponding JWPlatform video.

    """


def player_embed_url(key, player, format='js'):
    """
    Return a signed URL pointing to a player initialised with a specific media item.

    :param key: JWPlatform key for the media.
    :param player: JWPlatform player key.
    :param format: (optional) Either ``'js'`` or ``'html'`` depending on whether you want an
        embeddable player or a HTML page with a player on it.

    .. seealso::

        `JWPlatform endpoint documentation
        <https://developer.jwplayer.com/jw-platform/docs/delivery-api-reference/#!/players/get_players_content_id_player_id_embed_type>`_.

    """
    url = urllib.parse.urljoin(
        settings.JWPLATFORM_API_BASE_URL,
        '/players/{key}-{player}.{format}'.format(
            key=key, player=player, format=format))
    return signed_url(url)


def get_jwplatform_client():
    """
    Examine the settings and return an authenticated :py:class:`jwplatform.Client` instance.

    .. seealso::

        The `jwplatform module on GitHub <https://github.com/jwplayer/jwplatform-py>`_.

    """
    return jwplatform.Client(settings.JWPLATFORM_API_KEY, settings.JWPLATFORM_API_SECRET)


def key_for_media_id(media_id, preferred_media_type='video', client=None):
    """
    :param media_id: the SMS media ID of the required video
    :type media_id: int
    :param preferred_media_type: (optional) the preferred media type to return. One of ``'video'``
        or ``'audio'``.
    :param client: (options) an authenticated JWPlatform client as returned by
        :py:func:`.get_jwplatform_client`. If ``None``, call :py:func:`.get_jwplatform_client`.
    :raises: :py:class:`.VideoNotFoundError` if the media id does not correspond to a JWPlatform
        video.

    """
    client = client if client is not None else get_jwplatform_client()

    # The value of the sms_media_id custom property we search for
    media_id_value = 'media:{:d}:'.format(media_id)

    # Search for videos
    response = client.videos.list(**{
        'search:custom.sms_media_id': media_id_value,
    })

    # Loop through "videos" to find the preferred one based on mediatype
    video_resource = None
    for video in response.get('videos', []):
        # Sanity check: skip videos with wrong media id since video search is
        # not "is equal to", it is "contains".
        if video.get('custom', {}).get('sms_media_id') != media_id_value:
            continue

        # use this video if it has the preferred mediatype or if we have nothing
        # else
        if (video.get('mediatype') == preferred_media_type
                or video_resource is None):
            video_resource = video

    # If no video found, raise error
    if video_resource is None:
        raise VideoNotFoundError()

    # Check the video we found has a non-None key
    if video_resource.get('key') is None:
        raise VideoNotFoundError()

    return video_resource['key']


def get_acl(key, client=None):
    """

    :param key: JWPlatform key for the media.
    :param client: (options) an authenticated JWPlatform client as returned by
        :py:func:`.get_jwplatform_client`. If ``None``, call :py:func:`.get_jwplatform_client`.
    """
    client = client if client is not None else get_jwplatform_client()
    try:
        video = client.videos.show(video_key=key)
        field = video.get('video', {}).get('custom', {}).get('sms_acl', None)
        field_parts = field.split(":")
        assert (
            len(field_parts) == 3 and
            field_parts[0] == 'acl' and
            field_parts[2] == ''
        ), "sms_acl should be of the format 'acl:{ACL}:"
        return field_parts[1].split(',')
    except jwplatform.errors.JWPlatformNotFoundError as err:
        raise VideoNotFoundError(err)


def signed_url(url):
    """
    Augment a JWPlatform URL with an expiration time and a signature as outlined in `the jwplatform
    documentation on signatures
    <https://developer.jwplayer.com/jw-platform/docs/developer-guide/delivery-api/legacy-url-token-signing/>`_.

    The signature timeout is specified by the
    :py:data:`~smsjwplatform.defaultsettings.JWPLATFORM_SIGNATURE_TIMEOUT` setting.

    :param url: The JWPlatform API URL to add a query string to.

    :returns: the API URL with "exp" and "sig" query parameters appended.

    """
    # Implementation based on
    # https://support-static.jwplayer.com/API/python-example.txt
    secret = settings.JWPLATFORM_API_SECRET
    timeout = settings.JWPLATFORM_SIGNATURE_TIMEOUT
    path = urllib.parse.urlsplit(url).path
    expiry_timestamp = int(time.time()) + timeout
    sign_data = '%s:%d:%s' % (path.lstrip('/'), expiry_timestamp, secret)
    signature = hashlib.md5(sign_data.encode('ascii')).hexdigest()
    return urllib.parse.urljoin(url, '?' + urllib.parse.urlencode({
        'exp': expiry_timestamp, 'sig': signature
    }))
