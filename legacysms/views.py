"""
Django views.

"""
from django.conf import settings
from django.shortcuts import render, redirect

from smsjwplatform.acl import build_acl
from smsjwplatform import jwplatform as api

from . import redirect as legacyredirect


def embed(request, media_id):
    """
    :param request: the current request
    :param media_id: SMS media id of the required media
    :type media_id: int

    Render an embedded video/audio player based on the SMS media ID. If the ``format`` GET
    parameter is provided, it should be one of ``audio`` or ``video`` and this is used to specify
    the preferred media type.

    If no media matching the provided SMS media ID is found, a 404 response is generated.

    In :py:mod:`~.urls` this view is named ``smsjwplatform:embed``.

    """
    try:
        key = api.key_for_media_id(
            media_id, preferred_media_type=request.GET.get('format', 'video'))
    except api.VideoNotFoundError:
        # If we cannot find the item, simply redirect to the legacy SMS. We ignore the format
        # parameter here because this redirect will only be for new media items and the embedding
        # HTML no longer includes the format parameter.
        return legacyredirect.media_embed(media_id)

    if not has_permission(request.user, key):
        return render(
            request, 'smsjwplatform/401.html',
            {'login_url': '%s?next=%s' % (settings.LOGIN_URL, request.path)}
            if request.user.is_anonymous else {}
        )

    url = api.player_embed_url(key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'js')
    return render(request, 'smsjwplatform/embed.html', {
        'embed_url': url,
    })


def rss_media(request, media_id):
    try:
        key = api.key_for_media_id(media_id, preferred_media_type='video')
    except api.VideoNotFoundError:
        # If we cannot find the item, simply redirect to the legacy SMS.
        return legacyredirect.media_rss(media_id)

    return redirect(api.pd_api_url(f'/v2/media/{key}', format='mrss'))


def has_permission(user, key):
    """
    Get the media's ACL then builds a list on encapsulated ACEs then return's True
    if any one of them returns true
    """
    for ace in build_acl(api.get_acl(key)):
        if ace.has_permission(user):
            return True
    return False
