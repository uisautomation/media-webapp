"""
Interaction with the JWPlatform API.

"""
import hashlib
import math
import time
import urllib.parse

from django.conf import settings
import django.core.exceptions
import jwplatform
import jwt

from . import acl


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


class VideoPermissionDenied(django.core.exceptions.PermissionDenied):
    """
    A sub-class of :py:exc:`django.core.exceptions.PermissionDenied` used to indicate that the
    current user does not match the ACL of a video. See: :py:func:`~.Video.check_user_access`.

    """


class Video(dict):
    """
    A dict subclass representing a video resource object as returned by the JWPlatform API.

    This subclass provides some convenience accessors for various common resource keys but, since
    this is a dict subclass, the values can be retrieved using ``[]`` or ``get`` as per usual.

    """
    @property
    def key(self):
        """JWPlatform key for this video or ``None`` if it has none."""
        return self.get('key')

    @property
    def acl(self):
        """
        The parsed ACL custom prop on the video. If no ACL is present, the WORLD ACL is assumed.

        """
        field = self.get('custom', {}).get('sms_acl', 'acl:WORLD:')
        return parse_custom_field('acl', field).split(',')

    def check_user_access(self, user):
        """
        Check whether the specified Django user has permission to access this video.
        Raises :py:exc:`~.VideoPermissionDenied` if the user does not match the ACL.
        """
        for ace in acl.build_acl(self.acl):
            if ace.has_permission(user):
                return True
        raise VideoPermissionDenied()

    @classmethod
    def from_key(cls, key, client=None):
        """
        Return a :py:class:`Video` instance corresponding to the JWPlatform key passed.

        :param key: JWPlatform key for the media.
        :param client: (optional) an authenticated JWPlatform client as returned by
            :py:func:`.get_jwplatform_client`. If ``None``, call :py:func:`.get_jwplatform_client`.

        :raises: :py:exc:`jwplatform.errors.JWPlatformNotFoundError` if the video is not found.

        """
        client = client if client is not None else get_jwplatform_client()
        return cls(client.videos.show(video_key=key)['video'])

    @classmethod
    def from_media_id(cls, media_id, preferred_media_type='video', client=None):
        """
        Return a :py:class:`Video` instance which matches the passed legacy SMS media ID or raise
        :py:exc:`VideoNotFoundError` if no such video could be found.

        :param media_id: the SMS media ID of the required video
        :type media_id: int
        :param preferred_media_type: (optional) the preferred media type to return. One of
            ``'video'`` or ``'audio'``.
        :param client: (options) an authenticated JWPlatform client as returned by
            :py:func:`.get_jwplatform_client`. If ``None``, call :py:func:`.get_jwplatform_client`.
        :raises: :py:class:`.VideoNotFoundError` if the media id does not correspond to a
            JWPlatform video.

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
        for video_dict in response.get('videos', []):
            # Convert video dictionary to video resource object
            video = cls(video_dict)

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

        return video_resource


def parse_custom_field(expected_type, field):
    """
    Parses a custom field content of the form "<expected_type>:<value>:". Returns the value.
    Raises ValueError if the field is of the wrong form or type.
    """
    field_parts = field.split(":")
    if len(field_parts) != 3 or field_parts[0] != expected_type or field_parts[2] != '':
        raise ValueError(f"expected format '{expected_type}:value:")

    return field_parts[1]


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


def generate_token(resource):
    """
    Generate a signed JWT for the specified resource using the
    `procedure
    <https://developer.jwplayer.com/jw-platform/docs/developer-guide/delivery-api/url-token-signing/>`_
    outlined in the JWPlatform documentation.

    """
    # The following is lifted almost verbatim from JWPlatform's documentation.

    # Link is valid for 1hr but normalized to 3 minutes to promote better caching
    exp = math.ceil((time.time() + 3600)/180) * 180
    token_body = {"resource": resource, "exp": exp}

    return jwt.encode(token_body, settings.JWPLATFORM_API_SECRET, algorithm='HS256')


def pd_api_url(resource, **parameters):
    """
    Return a JWPlatform Platform Delivery API URL with the request has the appropriate JWT
    attached.

    :param str resource: path to resource, e.g. ``/v2/media/123456``. Must start with a slash.
    :param dict parameters: remaining keyword arguments are passed as URL parameters
    :return: response from API server.
    :rtype: requests.Response

    :raises ValueError: if the resource name does not start with a slash.

    .. seealso::

        Platform Delivery API reference at
        https://developer.jwplayer.com/jw-platform/docs/delivery-api-reference/.
    """
    # Validate the resource parameter
    if not resource.startswith('/'):
        raise ValueError('Resource name must have leading slash')

    # Construct parameters for URL including JWT
    url_params = {'token': generate_token(resource)}
    url_params.update(parameters)

    # Construct GET URL
    url = urllib.parse.urljoin(
        settings.JWPLATFORM_API_BASE_URL,
        resource + '?' + urllib.parse.urlencode(url_params)
    )

    return url