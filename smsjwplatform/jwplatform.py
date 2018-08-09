"""
Interaction with the JWPlatform API.

"""
import hashlib
import logging
import math
import re
import time
import urllib.parse

import requests
from django.conf import settings
import django.core.exceptions
import jwplatform
import jwt

from . import acl
from . import models

LOG = logging.getLogger(__name__)

# Default session used for making HTTP requests.
DEFAULT_REQUESTS_SESSION = requests.Session()


class VideoNotFoundError(RuntimeError):
    """
    The provided SMS media ID does not have a corresponding JWPlatform video.

    """


class UnparseableVideoError(RuntimeError):
    """
    The JWPlayer JSON response body was unparseable.

    """


def player_embed_url(key, player, format='js', base=None):
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
    base = base if base is not None else settings.JWPLATFORM_API_BASE_URL
    url = urllib.parse.urljoin(base, '/players/{key}-{player}.{format}'.format(
        key=key, player=player, format=format
    ))
    return signed_url(url)


def get_jwplatform_client():
    """
    Examine the settings and return an authenticated :py:class:`jwplatform.Client` instance.

    .. seealso::

        The `jwplatform module on GitHub <https://github.com/jwplayer/jwplatform-py>`_.

    """
    return jwplatform.Client(settings.JWPLATFORM_API_KEY, settings.JWPLATFORM_API_SECRET)


class ResourceACLPermissionDenied(django.core.exceptions.PermissionDenied):
    """
    A sub-class of :py:exc:`django.core.exceptions.PermissionDenied` used to indicate that the
    current user does not match the ACL of a video. See: :py:func:`~.Video.check_user_access`.

    """


class Resource(dict):
    """
    A dict subclass representing a media item or channel resource as returned by the JWPlatform
    API. This subsclass is specialised by the :py:class:`.Video` or :py:class:`.Channel` objects.

    """
    @property
    def key(self):
        """JWPlatform key for this resource or ``None`` if it has none."""
        return self.get('key')

    @property
    def acl(self):
        """
        The parsed ACL custom prop on the resource. If no ACL is present, the WORLD ACL is assumed.

        """
        field = parse_custom_field('acl', self.get('custom', {}).get('sms_acl', 'acl:WORLD:'))

        # Work around odd ACL entries. See uisautomation/sms2jwplayer#30.
        if field == "['']":
            return []

        return [acl.strip() for acl in field.split(',') if acl.strip() != '']

    def check_user_access(self, user):
        """
        Check whether the specified Django user has permission to access this resource.
        Raises :py:exc:`~.ResourceACLPermissionDenied` if the user does not match the ACL.
        """
        for ace in acl.build_acl(self.acl):
            if ace.has_permission(user):
                return True
        raise ResourceACLPermissionDenied()

    def get_poster_url(self, width=720):
        return settings.JWPLATFORM_API_BASE_URL + 'thumbs/{key}-{width}.jpg'.format(
            key=self.key, width=width)


class Video(Resource):
    """
    A dict subclass representing a video resource object as returned by the JWPlatform API.

    This subclass provides some convenience accessors for various common resource keys but, since
    this is a dict subclass, the values can be retrieved using ``[]`` or ``get`` as per usual.

    """
    @property
    def media_id(self):
        """
        The legacy SMS media id (or None if there is none)

        """
        field = self.get('custom', {}).get('sms_media_id')
        if field is None:
            return None
        return parse_custom_field('media', field)

    @classmethod
    def from_key(cls, key):
        """
        Return a :py:class:`Video` instance corresponding to the JWPlatform key passed.

        .. note::

            This method looks for videos by way of the
            :py:class:`~smsjwplatform.models.CachedResource` model and *not* by using the API
            directly.

        :param key: JWPlatform key for the media.

        :raises: :py:exc:`~.VideoNotFoundError` if the video is not found.

        """
        try:
            return cls(models.CachedResource.videos.get(key=key).data)
        except models.CachedResource.DoesNotExist:
            raise VideoNotFoundError()

    @classmethod
    def from_media_id(cls, media_id, preferred_media_type='video'):
        """
        Return a :py:class:`Video` instance which matches the passed legacy SMS media ID or raise
        :py:exc:`VideoNotFoundError` if no such video could be found.

        .. note::

            This method looks for videos by way of the
            :py:class:`~smsjwplatform.models.CachedResource` model and *not* by using the API
            directly.

        :param media_id: the SMS media ID of the required video
        :type media_id: int
        :param preferred_media_type: (optional) the preferred media type to return. One of
            ``'video'`` or ``'audio'``.
        :raises: :py:class:`.VideoNotFoundError` if the media id does not correspond to a
            JWPlatform video.

        """
        # The value of the sms_media_id custom property we search for
        media_id_value = 'media:{:d}:'.format(media_id)

        # Search for videos
        videos = (v.data for v in models.CachedResource.videos.filter(
            data__custom__sms_media_id=media_id_value
        ))

        # Loop through "videos" to find the preferred one based on mediatype
        video_resource = None
        for video_dict in videos:
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


class DeliveryVideo(Resource):
    """
    A dict subclass representing a video resource object as returned by the Delivery API.

    This subclass provides some convenience accessors for various common resource keys but, since
    this is a dict subclass, the values can be retrieved using ``[]`` or ``get`` as per usual.

    """
    @property
    def media_id(self):
        """
        The legacy SMS media id (or None if there is none)

        """
        field = self.get('sms_media_id')
        if field is None:
            return None
        return parse_custom_field('media', field)

    @property
    def acl(self):
        """
        The parsed ACL custom prop on the resource. If no ACL is present, the WORLD ACL is assumed.

        """
        field = parse_custom_field('acl', self.get('sms_acl', 'acl:WORLD:'))

        # Work around odd ACL entries. See uisautomation/sms2jwplayer#30.
        if field == "['']":
            return []

        return [acl.strip() for acl in field.split(',') if acl.strip() != '']

    @classmethod
    def from_key(cls, key, session=None):
        """
        Return a :py:class:`DeliveryVideo` instance corresponding to the JWPlatform key passed.

        :param key: JWPlatform key for the media.
        :param session: (optional) session used for making HTTP requests, if None, then a default
        is used.

        :raises: :py:exc:`VideoNotFoundError` if the video is not found.

        """
        session = session if session is not None else DEFAULT_REQUESTS_SESSION

        # Fetch the media download information from JWPlatform.
        response = session.get(
            pd_api_url(f'/v2/media/{key}', format='json'), timeout=5
        )

        if response.status_code == 404:
            LOG.warning("Couldn't find video for key '%s'", key)
            raise VideoNotFoundError

        # translate
        response.raise_for_status()

        # Parse response as JSON
        try:
            body = response.json()
        except Exception as e:
            message = 'Failed to parse response when retrieving video "%s": %s'.format(key, e)
            LOG.warning(message)
            raise UnparseableVideoError(message)

        item = body['playlist'][0]

        item['key'] = item.get('mediaid')
        item['date'] = item.get('pubdate')

        return cls(item)


class Channel(Resource):
    """
    A dict subclass representing a channel resource object as returned by the JWPlatform API.

    This subclass provides some convenience accessors for various common resource keys but, since
    this is a dict subclass, the values can be retrieved using ``[]`` or ``get`` as per usual.

    """
    @property
    def collection_id(self):
        """
        The legacy SMS collection id (or None if there is none)

        """
        field = self.get('custom', {}).get('sms_collection_id')
        if field is None:
            return None
        return parse_custom_field('collection', field)

    def get_poster_url(self):
        # TODO: find some solution for channel thumbnails
        field = self.get('custom', {}).get('sms_image_id')
        if field is None:
            return None

        image_id = parse_custom_field('image', field)

        # Work around an import script bug
        if image_id is None or image_id == 'None':
            return None

        return f'https://sms.cam.ac.uk/image/{image_id}'

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
        return cls(client.channels.show(channel_key=key)['channel'])

    @classmethod
    def list(cls, list_params={}, client=None):
        """
        Convenience wrapper around the ``channels.list`` JWPlatform API method. The channels
        returned are coerced into :py:class:`Video` instances.

        """
        client = client if client is not None else get_jwplatform_client()
        response = client.channels.list(**list_params)

        if 'channels' in response:
            response['channels'] = [cls(resource) for resource in response['channels']]

        return response


CUSTOM_FIELD_PATTERN = re.compile(r'^(?P<type>[^:]+):(?P<value>.*):$')


def parse_custom_field(expected_type, field):
    """
    Parses a custom field content of the form "<expected_type>:<value>:". Returns the value.
    Raises ValueError if the field is of the wrong form or type.
    """
    match = CUSTOM_FIELD_PATTERN.match(field)
    if not match or match.group('type') != expected_type:
        raise ValueError(f"expected format '{expected_type}:value:, value was '{field}'")

    return match.group('value')


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


def _generate_token(resource, now_timestamp):
    """
    Generate a signed JWT for the specified resource using the
    `procedure
    <https://developer.jwplayer.com/jw-platform/docs/developer-guide/delivery-api/url-token-signing/>`_
    outlined in the JWPlatform documentation.

    """
    # The following is lifted almost verbatim from JWPlatform's documentation.

    # Link is valid for 1hr but normalized to 3 minutes to promote better caching
    exp = math.ceil((now_timestamp + 3600)/180) * 180
    token_body = {"resource": resource, "exp": exp}

    return jwt.encode(token_body, settings.JWPLATFORM_API_SECRET, algorithm='HS256')


def pd_api_url(resource, now_timestamp=None, **parameters):
    """
    Return a JWPlatform Platform Delivery API URL with the request has the appropriate JWT
    attached.

    :param str resource: path to resource, e.g. ``/v2/media/123456``. Must start with a slash.
    :param int now_timestamp: the current UTC timestamp as returned by :py:func:`time.time`.
    :param dict parameters: remaining keyword arguments are passed as URL parameters
    :return: response from API server.
    :rtype: requests.Response

    If *now_timestamp* is ``None``, the value returned by :py:func:`time.time` is used.

    :raises ValueError: if the resource name does not start with a slash.

    .. seealso::

        Platform Delivery API reference at
        https://developer.jwplayer.com/jw-platform/docs/delivery-api-reference/.
    """
    # Validate the resource parameter
    if not resource.startswith('/'):
        raise ValueError('Resource name must have leading slash')

    now_timestamp = now_timestamp if now_timestamp is not None else time.time()

    # Construct parameters for URL including JWT
    url_params = {'token': _generate_token(resource, now_timestamp=now_timestamp)}
    url_params.update(parameters)

    # Construct GET URL
    url = urllib.parse.urljoin(
        settings.JWPLATFORM_API_BASE_URL,
        resource + '?' + urllib.parse.urlencode(url_params)
    )

    return url
