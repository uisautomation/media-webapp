"""
Uploading support for JWPlatform.

"""
import datetime

from django.utils import timezone

from mediaplatform import models as mpmodels

#: Lifetime of an upload URL
UPLOAD_URL_LIFETIME = datetime.timedelta(days=6)


def record_link_response(link_data, item):
    """
    Some JWP management API calls return a "link" dictionary in their response which represents an
    upload endpoint. This function implements the required string processing magic to turn that
    into a URL and stores that URL in the database as a
    :py:class:`mediaplatform.models.UploadEndpoint` object associated with the passed
    :py:class:`mediaplatform.models.MediaItem`.

    The default JWP upload link expiry is 7 days from creation. We assume the link has just been
    created and set an expiry of "now" plus :py:data:`~.UPLOAD_URL_LIFETIME`.

    """
    upload_url = (
        '{protocol}://{address}{path}?api_format=json&key={query[key]}'
        '&token={query[token]}'
    ).format(**link_data)

    # Parse response and create an upload endpoint. We mandate in the database that there can be
    # only one upload endpoint for a given MediaItem.
    mpmodels.UploadEndpoint.objects.filter(item=item).delete()
    mpmodels.UploadEndpoint.objects.create(
        url=upload_url, item=item, expires_at=timezone.now() + UPLOAD_URL_LIFETIME
    )
