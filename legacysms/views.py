"""
Django views.

"""
import logging
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
import requests

from mediaplatform import models as mpmodels

from . import redirect as legacyredirect
from . import models


LOG = logging.getLogger(__name__)

#: Default session used for making HTTP requests.
DEFAULT_REQUESTS_SESSION = requests.Session()


@xframe_options_exempt
def embed(request, media_id):
    """
    :param request: the current request
    :param media_id: SMS media id of the required media
    :type media_id: int

    Render an embedded video/audio player based on the SMS media ID. If the ``format`` GET
    parameter is provided, it should be one of ``audio`` or ``video`` and this is used to specify
    the preferred media type.

    If no media matching the provided SMS media ID is found, a 404 response is generated.

    In :py:mod:`~.urls` this view is named ``mediaplatform_jwp:embed``.

    """
    item = _find_media_item(media_id, request)

    # If we can't find the item, render a custom 404 error page.
    if item is None:
        return render(request, 'legacysms/embed_404.html', status=404)

    return redirect(reverse('ui:media_embed', kwargs={'pk': item.id}))


def rss_media(request, media_id):
    item = _find_media_item(media_id, request)

    # If we can't find the item, raise a 404.
    if item is None:
        raise Http404()

    return redirect(reverse('ui:media_item_rss', kwargs={'pk': item.id}))


#: Map between filename extensions passed to the download URL and the content type which should be
#: served. JWPlatform does not perform WEBM or MP3 encoding and so we simply use the MP4 version.
CONTENT_TYPE_FOR_DOWNLOAD_EXTENSION = {
    'mp4': 'video/mp4', 'webm': 'video/mp4', 'm4v': 'video/mp4',
    'mp3': 'audio/mp4', 'm4a': 'audio/mp4', 'aac': 'audio/mp4',
}


def download_media(request, media_id, clip_id, extension):
    item = _find_media_item(media_id, request)

    # If we can't find the item, return a 404 response
    if item is None:
        raise Http404()

    # Redirect to the source page
    return redirect(reverse('api:media_source', kwargs={'pk': item.id}))


def media(request, media_id):
    """
    :param request: the current request
    :param media_id: SMS media id of the required media
    :type media_id: int

    Redirect to the correct UI view for the specified SMS media IO. If no media matching the
    provided SMS media ID is found, a redirect back to the legacy SMS is generated.

    In :py:mod:`~.urls` this view is named ``legacysms:media``.

    """
    item = (
        mpmodels.MediaItem.objects.all().viewable_by_user(request.user)
        .filter(sms__id=media_id).first()
    )

    # If we can't find the item, redirect back to SMS to see if it knows about it
    if item is None:
        return legacyredirect.media_page(media_id)

    return redirect(reverse('ui:media_item', kwargs={'pk': item.id}))


def rss_collection(request, collection_id):
    playlist = _find_collection_playlist(collection_id, request)

    # If we can't find the playlist, raise a 404.
    if playlist is None:
        raise Http404()

    return redirect(reverse('ui:playlist_rss', kwargs={'pk': playlist.id}))


def _find_media_item(media_id, request):
    """
    Locates a media item for the passed SMS media id for the user in the passed request. If no such
    item can be found, return None.

    """
    return (
        mpmodels.MediaItem.objects.all().viewable_by_user(request.user)
        .filter(sms__id=media_id).first()
    )


def _find_collection_playlist(collection_id, request):
    """
    Locates a playlist for the passed SMS collection id for the user in the passed request. If no
    such playlist can be found, return None.

    """
    collection = models.Collection.objects.filter(id=collection_id).first()
    if collection is None:
        return None

    return (
        mpmodels.Playlist.objects.all().viewable_by_user(request.user)
        .filter(id=collection.playlist.id).first()
    )
