"""
Occasionally we may want to redirect incoming requests back to the legacy SMS. For example, if we
are asked to generate an embed view for a video which is not in the JWPlatform database, we don't
know if that is because the video doesn't exist or if that is because the video has not yet been
imported. In this case, we redirect back to a special SMS URL which handles the request for us.

"""
from urllib import parse as urlparse

from django.conf import settings
from django.shortcuts import redirect


def media_embed(media_id):
    """
    Returns a :py:class:`HttpResponse` which redirects back to the legacy embed view for the given
    media id. Raises :py:exc:`ValueError` if *media_id* is non-numeric.

    """
    return _redirect_relative(f'media/{media_id:d}/embed')


def media_rss(media_id):
    """
    Returns a :py:class:`HttpResponse` which redirects back to the legacy RSS feed for the given
    media id. Raises :py:exc:`ValueError` if *media_id* is non-numeric.

    """
    return _redirect_relative(f'rss/media/{media_id:d}')


def media_download(media_id, clip_id, extension):
    """
    Returns a :py:class:`HttpResponse` which redirects back to the legacy download link for the
    given media id. Raises :py:exc:`ValueError` if *media_id* or *clip_id* are non-numeric.

    """
    return _redirect_relative(f'_downloads/{media_id:d}/{clip_id:d}.{extension}')


def _redirect_relative(path):
    """
    Given a relative URL path, return the redirect to the full URL formed using the
    LEGACY_SMS_REDIRECT_BASE_URL setting.

    """
    return redirect(urlparse.urljoin(settings.LEGACY_SMS_REDIRECT_BASE_URL, path))
