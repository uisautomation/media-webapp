import datetime
import dateutil.parser

from django.db import models, transaction
from django.db.models import expressions, functions
from django.utils import timezone
import pytz

import mediaplatform.models as mpmodels
import mediaplatform_jwp.models as jwpmodels
import legacysms.models as legacymodels
import smsjwplatform.models as smsjwpmodels

from smsjwplatform import jwplatform as jwp


@transaction.atomic
def update_related_models_from_cache(update_all=False):
    """
    Atomically update the database to reflect the current state of the CachedResource table. If a
    video is deleted from JWP, the corresponding MediaItem is marked as deleted. Similarly, if it
    is deleted from the SMS (but is still in JWP for some reason), the legacysms.MediaItem model
    associated with the MediaItem is deleted.

    For video resources whose updated timestamp has increased, the JWP and SMS metadata is
    synchronised to mediaplatform.MediaItem or an associated legacysms.MediaItem as appropriate.

    The *update_all* flag may be set to True in which case a synchronisation of *all* MediaItems
    with the associated CachedResource is performed irrespective of the updated_at timestamp.

    TODO: no attempt is yet made to synchronise the edit permission with that of the containing
    collection for media items. This needs a bit more thought about how the SMS permission model
    maps into the new world.

    """
    # 1) Delete mediaplatform_jwp.Video objects which are no-longer hosted by JWP and mark the
    # corresponding media items as "deleted".
    #
    # After this stage, there will be no mediaplatform_jwp.Video, mediaplatform.MediaItem or
    # legacysms.MediaItem objects in the database which are reachable from a JWP video which is
    # no-longer hosted on JWP.

    # A query for JWP videos in our DB which are no-longer in JWPlatform
    deleted_jwp_videos = jwpmodels.Video.objects.exclude(
        key__in=smsjwpmodels.CachedResource.videos.values_list('key', flat=True))

    # A query for media items which are to be deleted because they relate to a JWP video which was
    # deleted
    deleted_media_items = (
        mpmodels.MediaItem.objects.filter(jwp__key__in=deleted_jwp_videos))

    # A query for legacysms media items which are to be deleted because they relate to a media item
    # which is to be deleted
    deleted_sms_media_items = (
        legacymodels.MediaItem.objects.filter(item__in=deleted_media_items))

    # Mark matching MediaItem models as deleted and delete corresponding SMS and JWP objects. The
    # order here is important since the queries are not actually run until the corresponding
    # update()/delete() calls.
    deleted_sms_media_items.delete()
    deleted_media_items.update(deleted_at=timezone.now())
    deleted_jwp_videos.delete()

    # 2) Update/create JWP video resources
    #
    # After this stage all mediaplatform_jwp.Video objects in the database should have the same
    # "updated" timestamp as the cached JWP resources and any newly appearing JWP videos should
    # have associated mediaplatform_jwp.Video objects.

    # A query which returns all the cached video resources which do not correspond to an existing
    # JWP video.
    new_video_resources = (
        smsjwpmodels.CachedResource.videos
        .exclude(key__in=jwpmodels.Video.objects.values_list('key', flat=True))
    )

    # Start creating a list of all JWP video object which were touched in this update
    updated_jwp_keys = [v.key for v in new_video_resources.only('key')]

    # Bulk insert Video objects for all new videos.
    jwpmodels.Video.objects.bulk_create([
        jwpmodels.Video(key=resource.key, updated=resource.data.get('updated', 0))
        for resource in new_video_resources
    ])

    # A subquery which returns the corresponding CachedResource's updated timestamp for a JWP
    # Video. We cannot simply use "data__updated" here because Django by design
    # (https://code.djangoproject.com/ticket/14104) does not support joined fields with update()
    # but the checks incorrectly interpret "data__updated" as a join and not a transform. Until
    # Django is fixed, we use a horrible workaround using RawSQL.  See
    # https://www.postgresql.org/docs/current/static/functions-json.html for the Postgres JSON
    # operators.
    matching_resource_updated = models.Subquery(
        smsjwpmodels.CachedResource.videos
        .filter(key=models.OuterRef('key'))
        .values_list(
            functions.Cast(expressions.RawSQL("data ->> 'updated'", []), models.BigIntegerField())
        )[:1]
    )

    # Add to our list of updated JWP videos
    updated_jwp_keys.extend([
        v.key
        for v in jwpmodels.Video.objects
        .filter(updated__lt=matching_resource_updated)
        .only('key')
    ])

    # For all mediaplatform_jwp.Video objects whose corresponding CachedResource's updated field is
    # later than the Video's updated field, update the Video.
    (
        jwpmodels.Video.objects
        .annotate(resource_updated=matching_resource_updated)
        .filter(updated__lt=models.F('resource_updated'))
        .update(updated=models.F('resource_updated'))
    )

    # 3) Insert missing mediaplatform.MediaItem objects
    #
    # After this stage, all mediaplatform_jwp.Video objects which lack a mediaplatform.MediaItem
    # will have one. The newly created mediaplatform.MediaItem objects will be blank but have an
    # updated_at timestamp well before the coressponding mediaplatform_jwp.Video object.

    # A queryset of all JWP Video objects which lack a mediaplatform.MediaItem annotated with the
    # data from the corresponding CachedResource
    videos_needing_items = (
        jwpmodels.Video.objects
        .filter(item__isnull=True)
        .annotate(data=models.Subquery(
            smsjwpmodels.CachedResource.videos
            .filter(key=models.OuterRef('key'))
            .values_list('data')[:1]
        ))
    )

    # For all videos needing a mediaplatform.MediaItem, create a blank one.
    jwp_keys_and_items = [
        (
            video.key,
            mpmodels.MediaItem(),
        )
        for video in videos_needing_items
    ]

    # Insert all the media items in an efficient manner.
    mpmodels.MediaItem.objects.bulk_create([
        item for _, item in jwp_keys_and_items
    ])

    # Since the bulk_create() call does not call any signal handlers, we need to manually create
    # all of the permissions for the new items.
    mpmodels.Permission.objects.bulk_create([
        mpmodels.Permission(allows_view_item=item) for _, item in jwp_keys_and_items
    ])
    mpmodels.Permission.objects.bulk_create([
        mpmodels.Permission(allows_edit_item=item) for _, item in jwp_keys_and_items
    ])

    # Add the corresponding media item link to the JWP videos.
    for key, item in jwp_keys_and_items:
        jwpmodels.Video.objects.filter(key=key).update(item=item)

    # 4) Update metadata for changed videos
    #
    # After this stage, all mediaplatform.MediaItem objects whose associated JWP video is one of
    # those in updated_jwp_keys need to be re-synchronised.  will have their metadata updated from
    # the JWP video's custom props. Note that legacysms.MediaItem objects associated with updated
    # mediaplatform.MediaItem objects will also be updated/created/deleted as necessary.

    # The media items which need update. We defer fetching all the metdata since we're going to
    # reset it anyway.
    updated_media_items = (
        mpmodels.MediaItem.objects.all()
        .select_related('view_permission', 'edit_permission')
        # updated_at is included because, without it, the field does not get updated on save() for
        # some reason
        .only('view_permission', 'edit_permission', 'jwp', 'sms', 'updated_at')
        .annotate(data=models.Subquery(
            smsjwpmodels.CachedResource.videos
            .filter(key=models.OuterRef('jwp__key'))
            .values_list('data')[:1]
        ))
    )

    # Unless we were asked to update the metadata in all objects, only update those which were last
    # updated before the corresponding JWP video resource. We use MEDIA_ITEM_FRESHNESS_THRESHOLD as
    # a "fudge factor" to make sure that we err on the side of updating too many objects rather
    # than relying on the JWP clock and our clock to be perfectly synchronised.
    if not update_all:
        updated_media_items = (
            updated_media_items
            .filter(jwp__key__in=updated_jwp_keys)
        )

    # Iterate over all updated media items and set the metadata
    max_tag_length = mpmodels.MediaItem._meta.get_field('tags').base_field.max_length
    type_map = {
        'video': mpmodels.MediaItem.VIDEO,
        'audio': mpmodels.MediaItem.AUDIO,
        'unknown': mpmodels.MediaItem.UNKNOWN,
    }
    for item in updated_media_items:
        # Skip items with no associated JWP video
        if item.data is None:
            continue

        video = jwp.Video(item.data)
        custom = video.get('custom', {})

        item.title = _default_if_none(video.get('title'), '')
        item.description = _default_if_none(video.get('description'), '')
        item.type = type_map[_default_if_none(video.get('mediatype'), 'unknown')]

        item.downloadable = 'True' == jwp.parse_custom_field(
                'downloadable', custom.get('sms_downloadable', 'downloadable:False:'))

        published_timestamp = video.get('date')
        if published_timestamp is not None:
            item.published_at = datetime.datetime.fromtimestamp(
                published_timestamp, pytz.utc)
        else:
            item.published_at = None

        item.duration = video.get('duration', 0)

        # The language should be a three letter code. Use [:3] to make sure that it always is even
        # if the JWP custom prop is somehow messed up.
        item.language = jwp.parse_custom_field(
                'language', custom.get('sms_language', 'language::'))[:3]

        item.copyright = jwp.parse_custom_field(
                'copyright', custom.get('sms_copyright', 'copyright::'))

        # Since tags have database enforced maximum lengths, make sure to truncate them if they're
        # too long. We also strip leading or trailing whitespace.
        item.tags = [
            tag.strip().lower()[:max_tag_length]
            for tag in jwp.parse_custom_field(
                'keywords', custom.get('sms_keywords', 'keywords::')
            ).split('|')
            if tag.strip() != ''
        ]

        # Update view permission
        item.view_permission.reset()

        for ace in video.acl:
            if ace == 'WORLD':
                item.view_permission.is_public = True
            elif ace == 'CAM':
                item.view_permission.is_signed_in = True
            elif ace.startswith('INST_'):
                item.view_permission.lookup_insts.append(ace[5:])
            elif ace.startswith('GROUP_'):
                item.view_permission.lookup_groups.append(int(ace[6:]))
            elif ace.startswith('USER_'):
                item.view_permission.crsids.append(ace[5:])

        item.view_permission.save()

        # Update edit permission
        item.edit_permission.reset()

        # TODO: the editors group from SMS has not been copied over to the JWP custom props yet. We
        # simply add the creator. Note that some of the videos in JWP have this prop be of the form
        # created_by:...: and some have creator:...: :(.
        try:
            creator = jwp.parse_custom_field(
                'created_by', custom.get('sms_created_by', 'created_by::'))
        except ValueError:
            creator = jwp.parse_custom_field(
                'creator', custom.get('sms_created_by', 'creator::'))

        item.edit_permission.crsids = [creator] if creator != '' else []
        item.edit_permission.save()

        # Update associated SMS media item (if any)
        sms_media_id = video.media_id
        if sms_media_id is not None:
            # Get or create associated SMS media item. Note that hasattr is recommended in the
            # Django docs as a way to determine isf a related objects exists.
            # https://docs.djangoproject.com/en/dev/topics/db/examples/one_to_one/
            if hasattr(item, 'sms') and item.sms is not None:
                sms_media_item = item.sms
            else:
                sms_media_item = legacymodels.MediaItem(id=sms_media_id)

            # Extract last updated timestamp. It should be an ISO 8601 date string.
            last_updated = jwp.parse_custom_field(
                'last_updated_at', custom.get('sms_last_updated_at', 'last_updated_at::'))

            # Update SMS media item
            sms_media_item.item = item
            if last_updated == '':
                sms_media_item.last_updated_at = None
            else:
                sms_media_item.last_updated_at = dateutil.parser.parse(last_updated)

            sms_media_item.save()
        else:
            # If there is no associated SMS media item, make sure that this item doesn't have one
            # pointing to it.
            if hasattr(item, 'sms') and item.sms is not None:
                item.sms.delete()

        item.save()


def _default_if_none(value, default):
    return value if value is not None else default
