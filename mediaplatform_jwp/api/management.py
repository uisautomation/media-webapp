"""
Interactions with the JWP management API.

"""
from mediaplatform_jwp.api import delivery as jwp

from mediaplatform_jwp import models
from mediaplatform_jwp import upload


def schedule_item_update(item):
    """
    Synchronises a JWP video to the passed :py:class:`mediaplatform.models.MediaItem`. If this
    necessitates creating a new JWP video, a new upload endpoint is also created. Upload endpoints
    are not created if the JWP video already exists.

    """
    # TODO: split this into an asynchronous task
    _perform_item_update(item)


def _perform_item_update(item):
    # Get a JWPlatform client
    jwp_client = jwp.get_jwplatform_client()

    video_resource = {
        'title': item.title,
        # HACK: JWP does not allow a blank description(!)
        'description': item.description if item.description != '' else ' ',

        # We need to populate the SMS fields so that jwpfetch does not overwrite this item
        'custom': {
            'sms_downloadable': 'downloadable:{}:'.format(item.downloadable),
            'sms_language': 'language:{}:'.format(item.language),
            'sms_copyright': 'copyright:{}:'.format(item.copyright),
            'sms_keywords': 'keywords:{}:'.format('|'.join(item.tags)),
        },
    }

    if item.published_at is not None:
        video_resource['date'] = int(item.published_at.timestamp())

    # If there are any permissions, add them too
    if hasattr(item, 'view_permission'):
        video_resource['custom']['sms_acl'] = 'acl:{}:'.format(
            _permission_to_acl(item.view_permission))

    # Convert the model updated_at field to a timestamp
    updated = int(item.updated_at.timestamp())

    if hasattr(item, 'jwp'):
        # Get/create the corresponding cached JWP resource
        video_key = item.jwp.key

        # Update the video using the JWP management API
        response = jwp_client.videos.update(
            http_method='POST', video_key=video_key, **_flatten_dict(video_resource))

        # Record the update
        item.jwp.updated = updated
        item.jwp.save()
    else:
        # Create the video using the JWP management API
        response = jwp_client.videos.create(
            http_method='POST', **_flatten_dict(video_resource))

        # Get/create the corresponding cached JWP resource
        video_key = response.get('media', {}).get('key')
        if video_key is None:
            raise RuntimeError('Unexpected response from JWP: {}'.format(repr(response)))

        # Create a JWP video model
        models.Video.objects.create(key=video_key, updated=updated, item=item)

    # If there was an upload link in the response, record it.
    link_data = response.get('link')
    if link_data is not None:
        upload.record_link_response(link_data, item)


def create_upload_endpoint(item):
    """
    Create an upload endpoint for a media item. Raises ValueError if the item does not have a
    corresponding JWP video

    """
    if not hasattr(item, 'jwp'):
        raise ValueError('MediaItem has no associated JWP video')

    # Get a JWPlatform client
    jwp_client = jwp.get_jwplatform_client()

    response = jwp_client.videos.update(
        http_method='POST', video_key=item.jwp.key, update_file=True)

    upload.record_link_response(response['link'], item)


def _permission_to_acl(permission):
    """
    Render a :py:class:`mediaplatform.models.Permission` instance as a SMS-style ACL

    """
    aces = []
    if permission.is_public:
        aces.append('WORLD')
    if permission.is_signed_in:
        aces.append('CAM')
    aces.extend(['USER_{}'.format(crsid) for crsid in permission.crsids])
    aces.extend(['GROUP_{}'.format(groupid) for groupid in permission.lookup_groups])
    aces.extend(['INST_{}'.format(instid) for instid in permission.lookup_insts])
    return ','.join(aces)


def _flatten_dict(d, prefix=[]):
    """
    Return a "flattened" dictionary suitable for passing to the JWP api. E.g.

    .. code::

        {
            'foo': 1,
            'bar': { 'buzz': 2 },
        }

    gets flattened to

    .. code::

        {
            'foo': 1,
            'bar.buzz': 2,
        }

    """
    rv = {}
    for k, v in d.items():
        if isinstance(v, dict):
            rv.update(_flatten_dict(v, prefix=prefix + [k]))
        else:
            rv['.'.join(prefix + [k])] = v
    return rv
