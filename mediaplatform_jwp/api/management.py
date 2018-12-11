"""
Interactions with the JWP management API.

"""
from django.contrib.sites.models import Site

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

    # Form a key for the current site replacing "."s with "_"s since JWP interprets "." specially.
    # NOTE: using get_current() here will use the SITE_ID setting so that must be set.
    current_site = Site.objects.get_current()
    safe_site_name = current_site.domain.replace('.', '_')

    video_resource = {
        'title': item.title,
        # HACK: JWP does not allow a blank description(!)
        'description': item.description if item.description != '' else ' ',

        'custom': {
            # We need to populate the SMS fields so that jwpfetch does not overwrite this item
            'sms_downloadable': 'downloadable:{}:'.format(item.downloadable),
            'sms_language': 'language:{}:'.format(item.language),
            'sms_copyright': 'copyright:{}:'.format(item.copyright),
            'sms_keywords': 'keywords:{}:'.format('|'.join(item.tags)),

            # Add custom props to the video to specify which site it is available on and which
            # media id it corresponds to.
            'site': {
                safe_site_name: {
                    'name': current_site.name,
                    'media_id': item.id,
                },
            }
        },
    }

    # Additional tags which should be set on the video. These tags are added in addition to any
    # existing tags.
    additional_tags = [f'sitedomain:{current_site.domain}']

    # Note: only has an effect if the item is being created
    if item.initially_fetched_from_url != '':
        video_resource['download_url'] = item.initially_fetched_from_url

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

        # Merge the tags in. JWP seems somewhat cavalier in whitespace surrounding tags and whether
        # the tags field comes back as null or "" so we have to be quite defensive.
        # See: RFC 1122 §1.2.2 and https://en.wikipedia.org/wiki/Robustness_principle
        existing_video = jwp_client.videos.show(video_key=video_key).get('video', {})
        existing_tags = [
            t.strip()
            for t in (existing_video.get('tags') or '').strip().split(',')
        ]
        for t in set(additional_tags) - set(existing_tags):
            existing_tags.append(t)
        video_resource['tags'] = ','.join(existing_tags)

        # Update the video using the JWP management API
        response = jwp_client.videos.update(
            http_method='POST', video_key=video_key, **_flatten_dict(video_resource))

        # Record the update
        item.jwp.updated = updated
        item.jwp.save()
    else:
        # Create the video using the JWP management API
        video_resource['tags'] = ','.join(additional_tags)
        response = jwp_client.videos.create(
            http_method='POST', **_flatten_dict(video_resource))

        # Get/create the corresponding cached JWP resource
        resource_data = response.get('media', {})
        video_key = resource_data.get('key')

        # For reasons best known to JWP, the response is different if download_url is set(!)
        if video_key is None:
            video_key = response.get('video', {}).get('key')

            if video_key is not None:
                # We need to fetch the resource again if download_url is set(!)
                resource_data = jwp_client.videos.show(
                    http_method='POST', video_key=video_key)['video']

        if video_key is None:
            raise RuntimeError('Unexpected response from JWP: {}'.format(repr(response)))

        # Create a JWP video model and update/create the associated cached resource for it
        resource, _ = models.CachedResource.objects.get_or_create(
            key=video_key, defaults={'data': resource_data}
        )
        models.Video.objects.create(key=video_key, updated=updated, item=item, resource=resource)

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
