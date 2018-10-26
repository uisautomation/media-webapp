import datetime
import dateutil.parser

from django.db import models, transaction
from django.db.models import expressions, functions
from django.utils import timezone
import pytz

import mediaplatform.models as mpmodels
import mediaplatform_jwp.models as jwpmodels
import legacysms.models as legacymodels
import mediaplatform_jwp.models as mediajwpmodels
from mediaplatform_jwp.api import delivery as jwp

from .signalhandlers import setting_sync_items


@transaction.atomic
def update_related_models_from_cache(update_all_videos=False):
    """
    Atomically update the database to reflect the current state of the CachedResource table. If a
    video is deleted from JWP, the corresponding MediaItem is marked as deleted. Similarly, if it
    is deleted from the SMS (but is still in JWP for some reason), the legacysms.MediaItem model
    associated with the MediaItem is deleted.

    For video resources whose updated timestamp has increased, the JWP and SMS metadata is
    synchronised to mediaplatform.MediaItem or an associated legacysms.MediaItem as appropriate.

    The update_all_videos flag may be set to True in which case a synchronisation of *all*
    MediaItems with the associated CachedResource is performed irrespective of the
    updated_at timestamp. Come what may, all channels are synchronised since there is no equivalent
    of the updated timestamp for JWP channels.

    TODO: no attempt is yet made to synchronise the edit permission with that of the containing
    collection for media items. This needs a bit more thought about how the SMS permission model
    maps into the new world.

    """
    # 1) Delete mediaplatform_jwp.{Video,Channel} objects which are no-longer hosted by JWP and
    # mark the corresponding media items/channels as "deleted".
    #
    # After this stage, there will be no mediaplatform_jwp.Video, mediaplatform.MediaItem,
    # legacysms.MediaItem, mediaplatform_jwp.Channel, mediaplatform.Channel or legacysms.Collection
    # objects in the database which are reachable from a JWP video which is no-longer hosted on
    # JWP.

    # A query for JWP videos/channels in our DB which are no-longer in JWPlatform
    deleted_jwp_videos = jwpmodels.Video.objects.exclude(
        key__in=mediajwpmodels.CachedResource.videos.values_list('key', flat=True))
    deleted_jwp_channels = jwpmodels.Channel.objects.exclude(
        key__in=mediajwpmodels.CachedResource.channels.values_list('key', flat=True))

    # A query for media items which are to be deleted because they relate to a JWP video which was
    # deleted
    deleted_media_items = (
        mpmodels.MediaItem.objects.filter(jwp__key__in=deleted_jwp_videos))

    # A query for channels which are to be deleted because they relate to a JWP video which was
    # deleted
    deleted_channels = (
        mpmodels.Channel.objects.filter(jwp__key__in=deleted_jwp_channels))

    # A query for legacysms media items which are to be deleted because they relate to a media item
    # which is to be deleted
    deleted_sms_media_items = (
        legacymodels.MediaItem.objects.filter(item__in=deleted_media_items))

    # A query for legacysms collections which are to be deleted because they relate to a channel
    # which is to be deleted
    deleted_sms_collections = (
        legacymodels.Collection.objects.filter(channel__in=deleted_channels))

    # Mark 'shadow' playlists associated with deleted collections as deleted.
    mpmodels.Playlist.objects.filter(sms__in=deleted_sms_collections).update(
        deleted_at=timezone.now()
    )

    # Mark matching MediaItem models as deleted and delete corresponding SMS and JWP objects. The
    # order here is important since the queries are not actually run until the corresponding
    # update()/delete() calls.
    deleted_sms_media_items.delete()
    deleted_media_items.update(deleted_at=timezone.now())
    deleted_jwp_videos.delete()

    # Move media items which are in deleted channels to have no channel, mark the original
    # channel as deleted and delete SMS/JWP objects
    mpmodels.MediaItem.objects.filter(channel__in=deleted_channels).update(channel=None)
    deleted_sms_collections.delete()
    deleted_channels.update(deleted_at=timezone.now())
    deleted_jwp_channels.delete()

    # 2) Update/create JWP video resources
    #
    # After this stage all mediaplatform_jwp.Video objects in the database should have the same
    # "updated" timestamp as the cached JWP resources and any newly appearing JWP videos should
    # have associated mediaplatform_jwp.Video objects.

    updated_jwp_video_keys = _ensure_resources(
        jwpmodels.Video, mediajwpmodels.CachedResource.videos)

    _ensure_resources(
        jwpmodels.Channel, mediajwpmodels.CachedResource.channels)

    # 3) Insert missing mediaplatform.MediaItem and mediaplatform.Channel objects
    #
    # After this stage, all mediaplatform_jwp.Video objects which lack a mediaplatform.MediaItem
    # and mediaplatform_jwp.Channel object which lack a mediaplatform.Channel will have one. The
    # newly created mediaplatform.MediaItem objects will be blank but have an updated_at timestamp
    # well before the corresponding mediaplatform_jwp.Video object.

    # A queryset of all JWP Video objects which lack a mediaplatform.MediaItem annotated with the
    # data from the corresponding CachedResource
    videos_needing_items = (
        jwpmodels.Video.objects
        .filter(item__isnull=True)
        .annotate(data=models.Subquery(
            mediajwpmodels.CachedResource.videos
            .filter(key=models.OuterRef('key'))
            .values_list('data')[:1]
        ))
    )

    # For all videos needing a mediaplatform.MediaItem, create a blank one for videos arising from
    # the SMS.
    jwp_keys_and_items = [
        (
            video.key,
            mpmodels.MediaItem(),
        )
        for video in videos_needing_items
        if getattr(video, 'data', {}).get('custom', {}).get('sms_media_id') is not None
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

    # Add the corresponding media item link to the JWP videos.
    for key, item in jwp_keys_and_items:
        jwpmodels.Video.objects.filter(key=key).update(item=item)

    # A queryset of all JWP Channel objects which lack a mediaplatform.Channel annotated with the
    # data from the corresponding CachedResource
    jw_channels_needing_channels = (
        jwpmodels.Channel.objects
        .filter(channel__isnull=True)
        .annotate(data=models.Subquery(
            mediajwpmodels.CachedResource.channels
            .filter(key=models.OuterRef('key'))
            .values_list('data')[:1]
        ))
    )

    # For all channels needing a mediaplatform.Channel, create a blank one.
    jwp_keys_and_channels = [
        (
            jw_channel.key,
            mpmodels.Channel(billing_account=_ensure_billing_account(
                jwp.parse_custom_field(
                    'instid',
                    jw_channel.data.get('custom', {}).get('sms_instid', 'instid::')
                )
            )),
        )
        for jw_channel in jw_channels_needing_channels
    ]

    # Insert all the channels in an efficient manner.
    mpmodels.Channel.objects.bulk_create([
        channel for _, channel in jwp_keys_and_channels
    ])

    # Since the bulk_create() call does not call any signal handlers, we need to manually create
    # all of the permissions for the new channels.
    mpmodels.Permission.objects.bulk_create([
        mpmodels.Permission(allows_edit_channel=channel) for _, channel in jwp_keys_and_channels
    ])

    # Add the corresponding media item link to the JWP channels.
    for key, channel in jwp_keys_and_channels:
        jwpmodels.Channel.objects.filter(key=key).update(channel=channel)

    # 4) Update metadata for changed videos
    #
    # After this stage, all mediaplatform.MediaItem objects whose associated JWP video is one of
    # those in updated_jwp_video_keys will have their metadata updated from the JWP video's custom
    # props. Note that legacysms.MediaItem objects associated with updated mediaplatform.MediaItem
    # objects will also be updated/created/deleted as necessary.

    # The media items which need update. We defer fetching all the metdata since we're going to
    # reset it anyway.
    updated_media_items = (
        mpmodels.MediaItem.objects.all()
        .select_related('view_permission')
        # updated_at is included because, without it, the field does not get updated on save() for
        # some reason
        .only('view_permission', 'jwp', 'sms', 'updated_at')
        .annotate(data=models.Subquery(
            mediajwpmodels.CachedResource.videos
            .filter(key=models.OuterRef('jwp__key'))
            .values_list('data')[:1]
        ))
    )

    # Unless we were asked to update the metadata in all objects, only update those which were last
    # updated before the corresponding JWP video resource OR were created by us.
    if not update_all_videos:
        updated_media_items = (
            updated_media_items
            .filter(
                models.Q(jwp__key__in=updated_jwp_video_keys) |
                models.Q(id__in=[item.id for _, item in jwp_keys_and_items])
            )
        )

    # Iterate over all updated media items and set the metadata
    max_tag_length = mpmodels.MediaItem._meta.get_field('tags').base_field.max_length
    type_map = {
        'video': mpmodels.MediaItem.VIDEO,
        'audio': mpmodels.MediaItem.AUDIO,
        'unknown': mpmodels.MediaItem.UNKNOWN,
    }

    # We'll be modifying the MediaItem objects to be consistent with the JWP videos. We *don't*
    # want the signal handlers then trying to modify the JWPlatform videos again so disable
    # MediaItem -> JWP syncing if it is enabled.
    with setting_sync_items(False):
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

            item.duration = _default_if_none(video.get('duration'), 0.)

            # The language should be a three letter code. Use [:3] to make sure that it always is
            # even if the JWP custom prop is somehow messed up.
            item.language = jwp.parse_custom_field(
                    'language', custom.get('sms_language', 'language::'))[:3]

            item.copyright = jwp.parse_custom_field(
                    'copyright', custom.get('sms_copyright', 'copyright::'))

            # Since tags have database enforced maximum lengths, make sure to truncate them if
            # they're too long. We also strip leading or trailing whitespace.
            item.tags = [
                tag.strip().lower()[:max_tag_length]
                for tag in jwp.parse_custom_field(
                    'keywords', custom.get('sms_keywords', 'keywords::')
                ).split('|')
                if tag.strip() != ''
            ]

            # Update view permission
            item.view_permission.reset()
            _set_permission_from_acl(item.view_permission, video.acl)
            item.view_permission.save()

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
                # If there is no associated SMS media item, make sure that this item doesn't have
                # one pointing to it.
                if hasattr(item, 'sms') and item.sms is not None:
                    item.sms.delete()

            item.save()

    # 5) Update metadata for changed channels
    #
    # After this stage, all mediaplatform.Channel objects whose associated JWP channel is one of
    # those in updated_jwp_channel_keys will have their metadata updated from the JWP channel's
    # custom props. Note that legacysms.Channel objects associated with updated
    # mediaplatform.Channel objects will also be updated/created/deleted as necessary.

    # The channels which need update. We defer fetching all the metdata since we're going to
    # reset it anyway.
    updated_channels = (
        mpmodels.Channel.objects.all()
        .select_related('edit_permission')
        # updated_at is included because, without it, the field does not get updated on save() for
        # some reason
        .only('edit_permission', 'jwp', 'sms', 'updated_at')
        .annotate(data=models.Subquery(
            mediajwpmodels.CachedResource.channels
            .filter(key=models.OuterRef('jwp__key'))
            .values_list('data')[:1]
        ))
    )

    for channel in updated_channels:
        # Skip channels with no associated JWP channel
        if channel.data is None:
            continue

        channel_data = jwp.Channel(channel.data)

        custom = channel_data.get('custom', {})

        # NB: The channel billing account is immutable and so we need not examine sms_instid here.
        channel.title = _default_if_none(channel_data.get('title'), '')
        channel.description = _default_if_none(channel_data.get('description'), '')

        # Update edit permission
        channel.edit_permission.reset()

        try:
            creator = jwp.parse_custom_field(
                'created_by', custom.get('sms_created_by', 'created_by::'))
        except ValueError:
            creator = jwp.parse_custom_field(
                'creator', custom.get('sms_created_by', 'creator::'))

        if creator != '' and creator not in channel.edit_permission.crsids:
            channel.edit_permission.crsids.append(creator)

        group_id = jwp.parse_custom_field(
            'groupid', custom.get('sms_groupid', 'groupid::'))
        if group_id != '' and group_id not in channel.edit_permission.lookup_groups:
            channel.edit_permission.lookup_groups.append(group_id)

        channel.edit_permission.save()

        # Update contents
        sms_collection_media_ids = [
            int(media_id.strip())
            for media_id in jwp.parse_custom_field(
                'media_ids', custom.get('sms_media_ids', 'media_ids::')
            ).split(',') if media_id.strip() != ''
        ]
        collection_media_ids = (
            mpmodels.MediaItem.objects.filter(sms__id__in=sms_collection_media_ids).only('id')
        )
        channel.items.set(collection_media_ids)

        # Update associated SMS collection (if any)
        sms_collection_id = channel_data.collection_id
        if sms_collection_id is not None:
            # Get or create associated SMS collection. Note that hasattr is recommended in the
            # Django docs as a way to determine if a related objects exists.
            # https://docs.djangoproject.com/en/dev/topics/db/examples/one_to_one/
            if hasattr(channel, 'sms') and channel.sms is not None:
                sms_channel = channel.sms
            else:
                sms_channel = legacymodels.Collection(id=sms_collection_id)

            # Extract last updated timestamp. It should be an ISO 8601 date string.
            last_updated = jwp.parse_custom_field(
                'last_updated_at', custom.get('sms_last_updated_at', 'last_updated_at::'))

            # Update SMS collection
            sms_channel.channel = channel
            if last_updated == '':
                sms_channel.last_updated_at = None
            else:
                sms_channel.last_updated_at = dateutil.parser.parse(last_updated)

            if sms_channel.playlist is None:
                # If the 'shadow' playlist doesn't exist, create it.
                sms_channel.playlist = mpmodels.Playlist(channel=channel)

            sms_channel.save()

            # Update the Playlist
            sms_channel.playlist.title = channel.title
            sms_channel.playlist.description = channel.description
            sms_channel.playlist.media_items = [item.id for item in collection_media_ids]
            sms_channel.playlist.save()
        else:
            # If there is no associated SMS collection, make sure that this channel doesn't have
            # one pointing to it.
            if hasattr(channel, 'sms') and channel.sms is not None:
                channel.sms.delete()

        channel.save()


def _ensure_billing_account(lookup_instid):
    """
    Return a billing account associated with the specified institution id if one exists or create
    one if not.

    """
    return mpmodels.BillingAccount.objects.get_or_create(
            defaults={'description': f'Lookup instutution {lookup_instid}'},
            lookup_instid=lookup_instid)[0]


def _default_if_none(value, default):
    return value if value is not None else default


def _set_permission_from_acl(permission, acl):
    """
    Given an ACL, update the passed permission to reflect it. The permission is not reset, nor is
    it save()-ed after the update.

    """
    for ace in acl:
        if ace == 'WORLD':
            permission.is_public = True
        elif ace == 'CAM':
            permission.is_signed_in = True
        elif ace.startswith('INST_'):
            permission.lookup_insts.append(ace[5:])
        elif ace.startswith('GROUP_'):
            permission.lookup_groups.append(ace[6:])
        elif ace.startswith('USER_'):
            permission.crsids.append(ace[5:])


def _ensure_resources(jwp_model, resource_queryset):
    """
    Given a model from mediaplatform_jwp and a queryset of CachedResource object corresponding to
    that model, make sure that objects of the appropriate model exist for each CachedResource
    object and that their updated timestamps are correct.

    Returns a list of all JWP resource keys for resources which were updated/created.
    """

    jwp_queryset = jwp_model.objects.all()

    # A query which returns all the cached video resources which do not correspond to an existing
    # JWP video.
    new_resources = (
        resource_queryset
        .exclude(key__in=jwp_queryset.values_list('key', flat=True))
    )

    # Start creating a list of all JWP video object which were touched in this update
    updated_jwp_keys = [v.key for v in new_resources.only('key')]

    # Bulk insert objects for all new resources.
    jwp_queryset.bulk_create([
        jwp_model(key=resource.key, updated=resource.data.get('updated', 0), resource=resource)
        for resource in new_resources
    ])

    # A subquery which returns the corresponding CachedResource's updated timestamp for a JWP
    # Video. We cannot simply use "data__updated" here because Django by design
    # (https://code.djangoproject.com/ticket/14104) does not support joined fields with update()
    # but the checks incorrectly interpret "data__updated" as a join and not a transform. Until
    # Django is fixed, we use a horrible workaround using RawSQL.  See
    # https://www.postgresql.org/docs/current/static/functions-json.html for the Postgres JSON
    # operators.
    matching_resource_updated = models.Subquery(
        resource_queryset
        .filter(key=models.OuterRef('key'))
        .values_list(
            functions.Cast(expressions.RawSQL("data ->> 'updated'", []), models.BigIntegerField())
        )[:1]
    )

    # Add to our list of updated JWP videos
    updated_jwp_keys.extend([
        v.key
        for v in jwp_queryset
        .filter(updated__lt=matching_resource_updated)
        .only('key')
    ])

    # For all objects whose corresponding CachedResource's updated field is later than the object's
    # updated field, update the object.
    (
        jwp_queryset
        .annotate(resource_updated=matching_resource_updated)
        .filter(updated__lt=models.F('resource_updated'))
        .update(updated=models.F('resource_updated'))
    )

    return updated_jwp_keys
