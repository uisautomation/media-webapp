"""
Django views.

"""
import logging
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
import requests

from mediaplatform_jwp.api import delivery as api
from mediaplatform import models as mpmodels

from . import redirect as legacyredirect


LOG = logging.getLogger(__name__)

#: Default session used for making HTTP requests.
DEFAULT_REQUESTS_SESSION = requests.Session()


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
    item = (
        mpmodels.MediaItem.objects.all().viewable_by_user(request.user)
        .filter(sms__id=media_id).first()
    )

    # If we can't find the item, render the custom 404 error page from the api application.
    if item is None:
        return render(request, 'api/embed_404.html', status=404)

    return redirect(reverse('api:media_embed', kwargs={'pk': item.id}))


def rss_media(request, media_id):
    try:
        video = api.Video.from_media_id(media_id, preferred_media_type='video')
    except api.VideoNotFoundError:
        # If we cannot find the item, simply redirect to the legacy SMS.
        return legacyredirect.media_rss(media_id)

    video.check_user_access(request.user)

    return redirect(api.pd_api_url(f'/v2/media/{video.key}', format='mrss'))


#: Map between filename extensions passed to the download URL and the content type which should be
#: served. JWPlatform does not perform WEBM or MP3 encoding and so we simply use the MP4 version.
CONTENT_TYPE_FOR_DOWNLOAD_EXTENSION = {
    'mp4': 'video/mp4', 'webm': 'video/mp4', 'm4v': 'video/mp4',
    'mp3': 'audio/mp4', 'm4a': 'audio/mp4', 'aac': 'audio/mp4',
}


def download_media(request, media_id, clip_id, extension):
    # NB: clip_id is ignored but we require it for two reasons: 1) compatibility with the legacy
    # SMS URL scheme and 2) so that we know which URL to redirect to if the corresponding media
    # item cannot be found in the JWPlatform DB.

    # Locate the matching JWPlatform video resource.
    try:
        video = api.Video.from_media_id(media_id, preferred_media_type='video')
    except api.VideoNotFoundError:
        # If we cannot find the item, simply redirect to the legacy SMS.
        LOG.info('download: failed to find matching video for media id %s', media_id)
        return legacyredirect.media_download(media_id, clip_id, extension)

    video.check_user_access(request.user)

    # Fetch the media download information from JWPlatform.
    try:
        r = DEFAULT_REQUESTS_SESSION.get(api.pd_api_url(f'/v2/media/{video.key}', format='json'),
                                         timeout=5)
    except requests.Timeout:
        LOG.warn('Timed out when retrieving information on video "%s" from JWPlatform', video)
        return HttpResponse(status=502)  # Bad gateway

    # Check that the call to JWPlatform succeeded.
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        LOG.warn('Got HTTP error when retrieving information on video "%s" from JWPlatform', video)
        LOG.warn('Error was: %s', e)
        return HttpResponse(status=502)  # Bad gateway

    # Parse response as JSON
    try:
        media_info = r.json()
    except Exception as e:
        LOG.warn(('Failed to parse JSON response when retrieving information on video "%s" from '
                  'JWPlatform'), video)
        LOG.warn('Error was: %s', e)
        return HttpResponse(status=502)  # Bad gateway

    # The response should be of the following form according to
    # https://developer.jwplayer.com/jw-platform/docs/delivery-api-reference/#!/media/get_v2_media_media_id
    #
    #   {
    #       "playlist": [
    #           {
    #               "sources": [
    #                   {
    #                       "width": <number>, "height": <number>, "file": <url>,
    #                       "type": <mime-type>
    #                   }
    #               ]
    #           }
    #       ]
    #   }
    #
    # In accordance with RFC 1122 § 1.2.2, we are "liberal in what we accept" when trying to get
    # the list of sources:
    try:
        playlist_item = media_info.get('playlist', [])[0]
    except IndexError:
        playlist_item = {}
    sources = playlist_item.get('sources', [])

    # We now need to find *which* video/audio source to redirect the user back to. Firstly,
    # determine which content/type we're looking for based on the extension. If we know of no such
    # content type, return a 404 response. We don't redirect back to the legacy SMS here because we
    # want to know earlier rather than later if the list of extensions in
    # CONTENT_TYPE_FOR_DOWNLOAD_EXTENSION is incomplete and a 404 is a louder signal than a
    # redirect :).
    try:
        desired_content_type = CONTENT_TYPE_FOR_DOWNLOAD_EXTENSION[extension.lower()]
    except KeyError:
        LOG.info('Could not match extension "%s" to a known content type', extension)
        raise Http404('Unknown extension: %s'.format(extension))

    # Filter the sources by this content type and then find the one with the largest height.
    # We assume that the tallest source is approximately the highest quality version available.
    sources_with_correct_type = [
        source for source in sources if source.get('type', '') == desired_content_type
    ]

    # If the filtered sources list is empty, redirect back to the legacy SMS to try and deal with
    # it.
    if len(sources_with_correct_type) == 0:
        LOG.info('download: failed to find source of content type %s for media id %s',
                 desired_content_type, media_id)
        return legacyredirect.media_download(media_id, clip_id, extension)

    # Find best source. I.e. the one with greatest height
    best_source = sources_with_correct_type[0]
    for candidate_source in sources_with_correct_type[1:]:
        if candidate_source.get('height', 0) > best_source.get('height', 0):
            best_source = candidate_source

    # Get the source URL
    try:
        url = best_source['file']
    except KeyError:
        LOG.warn('download: source is missing file key: %s', best_source)
        return legacyredirect.media_download(media_id, clip_id, extension)

    # Redirect to the direct download URL for the media item.
    return redirect(url)


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
