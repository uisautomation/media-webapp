import dataclasses
import itertools
import secrets
import typing

import automationlookup
from django.conf import settings
import django.contrib.postgres.fields as pgfields
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from iso639 import languages


#: The number of bytes of entropy in the tokens returned by _make_token.
_TOKEN_ENTROPY = 8


def _make_token():
    """
    Return a cryptographically random URL-safe token. The implementation returns an id with
    :py:data:`_TOKEN_ENTROPY` bytes of entropy with length :py:data:`_TOKEN_LENGTH`.

    For some additional background, see Tom Scott's informative video on ids for websites at
    https://www.youtube.com/watch?v=gocwRvLhDf8.

    Going forward, we probably want to run these past a black list of "naughty" words. :)

    """
    return secrets.token_urlsafe(_TOKEN_ENTROPY)


#: The number of characters in the tokens returned by _make_token. This matches the length of the
#: ids used by YouTube which suggests there'll be enough entropy for the time being.
_TOKEN_LENGTH = len(_make_token())


def _blank_array():
    """
    Return a new blank array. Used for the default in ArrayField-s below because Django's migration
    system cannot handle serialising lambdas.

    """
    return []


class PermissionQuerySetMixin:
    def _permission_condition(self, fieldname, user):
        """
        Return a queryset expression for the permission field "fieldname" which is True if the
        passed user has that permission.

        """
        # Start with the condition that the item must be public
        condition = models.Q(**{fieldname + '__is_public': True})

        # If a non-None user was passed and the user is not anonymous, we can add additional ways
        # the item can be viewed
        if user is not None and not user.is_anonymous:
            groupids, instids = _lookup_groupids_and_instids_for_user(user)

            # Irrespective of user groups/institutions, any signed in user has the is_signed_in
            # permission
            condition |= models.Q(**{fieldname + '__is_signed_in': True})

            # The user may also be explicitly mentioned in the list of allowed crsids
            condition |= models.Q(**{fieldname + '__crsids__contains': [user.username]})

            # The user's lookup groups may overlap with the allowed set
            condition |= models.Q(**{fieldname + '__lookup_groups__overlap': groupids})

            # The user's lookup institutions may overlap with the allowed set
            condition |= models.Q(**{fieldname + '__lookup_insts__overlap': instids})

        return condition


class MediaItemQuerySet(PermissionQuerySetMixin, models.QuerySet):

    def _viewable_condition(self, user):
        # The item can be viewed if any of the following are satisfied:
        #
        # 1. The user has view permission and the item is published.
        # 2. The user has edit permission as determined by _editable_condition().
        # 3. The user has the "mediaplatform.view_mediaitem" permission.

        # If the user has the correct permission, return a tautology. There doesn't appear to be a
        # cleaner way to express "True" as a Django Q() expression
        if user is not None and user.has_perm('mediaplatform.view_mediaitem'):
            return models.Q(id=models.F('id'))

        # An item is "published" if it either has no publication time or the publication time is in
        # the past.
        published = models.Q(published_at__isnull=True) | models.Q(published_at__lt=timezone.now())

        return (
            (self._permission_condition('view_permission', user) & published) |
            self._editable_condition(user)
        )

    def annotate_viewable(self, user, name='viewable'):
        """
        Annotate the query set with a boolean indicating if the user can view the item.

        """
        return self.annotate(**{
            name: models.Case(
                models.When(self._viewable_condition(user), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def viewable_by_user(self, user):
        """
        Filter the queryset to only those items which can be viewed by the passed Django user.

        """
        return self.filter(self._viewable_condition(user))

    def _editable_condition(self, user):
        # For the moment, we make sure that *all* SMS-derived objects are immutable to guard
        # against accidents.
        return (
            self._permission_condition('channel__edit_permission', user) &
            models.Q(sms__isnull=True) &
            models.Q(channel__sms__isnull=True)
        )

    def annotate_editable(self, user, name='editable'):
        """
        Annotate the query set with a boolean indicating if the user can edit the item.

        """
        return self.annotate(**{
            name: models.Case(
                models.When(self._editable_condition(user), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def editable_by_user(self, user):
        """
        Filter the queryset to only those items which can be edited by the passed Django user.

        """
        return self.filter(self._editable_condition(user))

    def _downloadable_condition(self, user):
        # The item can be downloaded if any of the following are satisfied:
        #
        # 1. The downloadable flag is set on the item.
        # 2. The user has the "mediaplatform.download_mediaitem" permission.

        # If the user has the correct permission, return a tautology. There doesn't appear to be a
        # cleaner way to express "True" as a Django Q() expression
        if user is not None and user.has_perm('mediaplatform.download_mediaitem'):
            return models.Q(id=models.F('id'))

        return models.Q(downloadable=True)

    def annotate_downloadable(self, user, name='downloadable_by_user'):
        """
        Annotate the query set with a boolean indicating if the user can download the item. To
        avoid clashing with the model's downloadable flag, the annotation is called
        "downloadable_by_user".

        """
        return self.annotate(**{
            name: models.Case(
                models.When(self._downloadable_condition(user), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def downloadable_by_user(self, user):
        """
        Filter the queryset to only those items which can be downloaded by the passed Django user.

        """
        return self.filter(self._downloadable_condition(user))


class MediaItemManager(models.Manager):
    """
    An object manager for :py:class:`~.MediaItem` objects. Accepts an additional named parameter
    *include_deleted* which specifies if the default queryset should include deleted items.

    """
    def __init__(self, *args, include_deleted=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._include_deleted = include_deleted

    def get_queryset(self):
        qs = MediaItemQuerySet(self.model, using=self._db)
        if not self._include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def create_for_user(self, user, **kwargs):
        """
        Convenience wrapper for create() which will create an item but also give the passed user
        view and edit permissions if the user is not anonymous.

        """
        obj = self.create(**kwargs)

        if user is not None and not user.is_anonymous:
            # Due to Django ORM oddness, we need to re-fetch the object to correctly modify
            # permissions otherwise the ORM gets confused
            new_obj = (
                self.all()
                .only()
                .select_related('view_permission')
                .get(id=obj.id)
            )
            new_obj.view_permission.crsids.append(user.username)
            new_obj.view_permission.save()

        return obj


class MediaItem(models.Model):
    """
    An individual media item in the media platform.

    Most fields in this model can store blank values since they are synced from external providers
    who may not have the degree of rigour we want. For the same reason, we have default values for
    most fields.

    """
    @dataclasses.dataclass
    class Source:
        """An encoded media stream for a media item."""

        #: MediaItem for this source (post Python3.7, we'll be able to refer to MediaItem as the
        #: type.)
        item: object

        #: Media type of the stream
        mime_type: str

        #: URL pointing to this source
        url: str

        #: Width of the stream or None if this is an audio stream
        width: typing.Optional[int] = None

        #: Height of the stream or None if this is an audio stream
        height: typing.Optional[int] = None

    class Meta:
        permissions = (
            ('download_mediaitem', 'Can download media associated with a media item'),
        )

    VIDEO = 'video'
    AUDIO = 'audio'
    UNKNOWN = 'unknown'
    TYPE_CHOICES = ((VIDEO, 'Video'), (AUDIO, 'Audio'))

    LANGUAGE_CHOICES = tuple(itertools.chain([('', 'None')], sorted(
        ((language.part3, language.name) for language in languages if language.part3 != ''),
        key=lambda choice: choice[1]
    )))

    #: Object manager. See :py:class:`~.MediaItemManager`. The objects returned by this manager do
    #: not include deleted objects. See :py:attr:\~.objects_including_deleted`.
    objects = MediaItemManager()

    #: Object manager whose objects include the deleted items. This has been separated out into a
    #: separate manager to avoid inadvertently including deleted objects in a query
    objects_including_deleted = MediaItemManager(include_deleted=True)

    #: Primary key
    id = models.CharField(
        max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: Channel which contains media item - if NULL, then the media item is in no channel.
    channel = models.ForeignKey(
        'Channel', help_text='Channel containing media item', null=True,
        on_delete=models.SET_NULL, related_name='items')

    #: Media item title
    title = models.TextField(help_text='Title of media item', blank=True, default='')

    #: Media item description
    description = models.TextField(help_text='Description of media item', blank=True, default='')

    #: Duration
    duration = models.FloatField(editable=False, help_text='Duration of video', default=0.)

    #: Type of media
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=UNKNOWN, editable=False,
        help_text='Type of media (video, audio or unknown)')

    #: Publication date
    published_at = models.DateTimeField(
        default=timezone.now, help_text='Date from which video is visible')

    #: Downloadable flag
    downloadable = models.BooleanField(
        default=False,
        help_text='If this item can be viewed, can it also be downloaded?')

    #: ISO 693-3 language code
    language = models.CharField(
        max_length=3, default='', blank=True, choices=LANGUAGE_CHOICES,
        help_text=(
            'ISO 639-3 three letter language code describing majority language used in this item'
        )
    )

    #: Video copyright
    copyright = models.TextField(
        blank=True, default='', help_text='Free text describing Copyright holder')

    #: List of tags for video
    tags = pgfields.ArrayField(models.CharField(max_length=256), default=_blank_array, blank=True,
                               help_text='Tags/keywords for item')

    #: Creation time
    created_at = models.DateTimeField(auto_now_add=True)

    #: Last update time
    updated_at = models.DateTimeField(auto_now=True)

    #: Deletion time. If non-NULL, the item has been "deleted" and should not usually be visible.
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{} ("{}")'.format(self.id, self.title)

    @cached_property
    def sources(self):
        """
        A list of :py:class:`~.MediaItem.Source` instances representing the raw media sources for
        this media item. This list is populated irrespective of the downloadable flag.

        """
        if not hasattr(self, 'jwp'):
            return []
        return self.jwp.sources

    @cached_property
    def fetched_analytics(self):
        """
        A cached property which returns legacy statistics if the media item is a legacy item.

        """
        return self.sms.fetch_analytics() if hasattr(self, 'sms') else []

    @cached_property
    def fetched_size(self):
        """
        A cached property which returns the storage size of the video in bytes (the sum of all the
        sources). Returns 0 if the size isn't available.

        """
        return int(
            getattr(
                getattr(getattr(self, 'jwp', {}), 'resource', {}), 'data', {}
            ).get('size', '0')
        )

    def get_embed_url(self):
        """
        Return a URL suitable for use in an IFrame which will render this media. This URL renders
        the media unconditionally; it does not respect any view permissions.

        """
        if not hasattr(self, 'jwp'):
            return None
        return self.jwp.embed_url


class Permission(models.Model):
    """
    Specify whether a user has permission to perform some action.

    A user has permission to perform the action if *any* of the following are true:

    * They have a crsid and that crsid appears in :py:attr:`~.crsids`
    * The lookup groupid of a lookup group which they are a member of appears in
      :py:attr:`~.lookup_groups`
    * The instid of an an institution they are a member of appears in
      :py:attr:`~.lookup_insts`
    * The :py:attr:`~.is_public` flag is ``True``
    * The user is not anonymous and :py:attr:`is_signed_in` is ``True``

    """
    #: Primary key
    id = models.CharField(
        max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: MediaItem whose view permission is this object
    allows_view_item = models.OneToOneField(
        MediaItem, on_delete=models.CASCADE, related_name='view_permission', editable=False,
        null=True
    )

    #: Channel whose edit permission is this object
    allows_edit_channel = models.OneToOneField(
        'Channel', on_delete=models.CASCADE, related_name='edit_permission', editable=False,
        null=True
    )

    #: Playlist whose view permission is this object
    #: It looks like an SMS collection is ALWAYS public, which makes this property redundant.
    #: However, for now, we leave it here and set is_public=True in the
    # _playlist_post_save_handler(). TODO remove this at some later date.
    allows_view_playlist = models.OneToOneField(
        'Playlist', on_delete=models.CASCADE, related_name='view_permission', editable=False,
        null=True
    )

    #: List of crsids of users with this permission
    crsids = pgfields.ArrayField(models.TextField(), blank=True, default=_blank_array)

    #: List of lookup groups which users with this permission belong to
    lookup_groups = pgfields.ArrayField(models.TextField(), blank=True, default=_blank_array)

    #: List of lookup institutions which users with this permission belong to
    lookup_insts = pgfields.ArrayField(models.TextField(), blank=True, default=_blank_array)

    #: Do all users (including anonymous ones) have this permission?
    is_public = models.BooleanField(default=False)

    #: Do all signed in (non-anonymous) users have this permission?
    is_signed_in = models.BooleanField(default=False)

    def __str__(self):
        if self.is_public:
            return 'Public'

        clauses = []
        if self.is_signed_in:
            clauses.append('is signed in')
        if len(self.crsids) != 0:
            clauses.append('crsid \N{ELEMENT OF} {{ {} }}'.format(', '.join(self.crsids)))
        if len(self.lookup_groups) != 0:
            clauses.append('lookup \N{ELEMENT OF} {{ {} }}'.format(
                ', '.join(self.lookup_groups)))
        if len(self.lookup_insts) != 0:
            clauses.append('lookup inst \N{ELEMENT OF} {{ {} }}'.format(
                ', '.join(self.lookup_insts)))

        if len(clauses) == 0:
            return 'Nobody'

        return ' OR '.join(clauses)

    def reset(self):
        """Reset this permission to the "allow nobody" state."""
        self.crsids = []
        self.lookup_groups = []
        self.lookup_insts = []
        self.is_public = False
        self.is_signed_in = False


class UploadEndpoint(models.Model):
    """
    An endpoint which can be used to upload a media item.

    """
    #: Primary key
    id = models.CharField(
        max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: URL for upload
    url = models.URLField(editable=False, help_text='URL to POST file data to')

    #: Related media item
    item = models.OneToOneField(
        MediaItem, editable=False, help_text='item this upload URL is for',
        on_delete=models.CASCADE, related_name='upload_endpoint')

    #: Date and time at which this upload URL will expire
    expires_at = models.DateTimeField(editable=False, help_text='Expiry time of URL')


class ChannelQuerySet(PermissionQuerySetMixin, models.QuerySet):
    def annotate_viewable(self, user, name='viewable'):
        """
        Annotate the query set with a boolean indicating if the user can view the channel.

        This is always true but this method is provided for compatibility with code shared between
        media items and channels.

        """
        return self.annotate(**{name: models.Value(True, output_field=models.BooleanField())})

    def viewable_by_user(self, user):
        """
        Filter the queryset to only those items which can be viewed by the passed Django user.

        This is a no-op filter but this method is provided for compatibility with code shared
        between media items and channels.

        """
        return self

    def _editable_condition(self, user):
        # For the moment, we make sure that *all* SMS-derived objects are immutble to guard against
        # accidents.
        return (
            self._permission_condition('edit_permission', user) &
            models.Q(sms__isnull=True)
        )

    def annotate_editable(self, user, name='editable'):
        """
        Annotate the query set with a boolean indicating if the user can edit the item.

        """
        return self.annotate(**{
            name: models.Case(
                models.When(
                    self._editable_condition(user),
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def editable_by_user(self, user):
        """
        Filter the queryset to only those items which can be edited by the passed Django user.

        """
        return self.filter(self._editable_condition(user))


class ChannelManager(models.Manager):
    """
    An object manager for :py:class:`~.Channel` objects. Accepts an additional named parameter
    *include_deleted* which specifies if the default queryset should include deleted items.

    """
    def __init__(self, *args, include_deleted=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._include_deleted = include_deleted

    def get_queryset(self):
        qs = ChannelQuerySet(self.model, using=self._db)
        if not self._include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def create_for_user(self, user, **kwargs):
        """
        Convenience wrapper for create() which will create a channel but also give the passed user
        edit permissions if the user is not anonymous.

        """
        obj = self.create(**kwargs)

        if user is not None and not user.is_anonymous:
            # Due to Django ORM oddness, we need to re-fetch the object to correctly modify
            # permissions otherwise the ORM gets confused
            new_obj = (
                self.all()
                .only()
                .select_related('edit_permission')
                .get(id=obj.id)
            )
            new_obj.edit_permission.crsids.append(user.username)
            new_obj.edit_permission.save()

        return obj


class Channel(models.Model):
    """
    An individual channel in the media platform.

    """
    #: Object manager. See :py:class:`~.ChannelManager`. The objects returned by this manager do
    #: not include deleted objects. See :py:attr:\~.objects_including_deleted`.
    objects = ChannelManager()

    #: Object manager whose objects include the deleted items. This has been separated out into a
    #: separate manager to avoid inadvertently including deleted objects in a query
    objects_including_deleted = ChannelManager(include_deleted=True)

    #: Primary key
    id = models.CharField(
        max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: Channel title
    title = models.TextField(help_text='Title of the channel', blank=False)

    #: Channel description
    description = models.TextField(help_text='Description of the channel', blank=True, default='')

    #: "Owning" lookup institution id. We default to the blank string but, aside from "special"
    #: internal channels, there should always be a lookup institution.
    owning_lookup_inst = models.CharField(
        max_length=255, blank=False, default='',
        help_text='Lookup instid for institution which "owns" this channel')

    #: Creation time
    created_at = models.DateTimeField(auto_now_add=True)

    #: Last update time
    updated_at = models.DateTimeField(auto_now=True)

    #: Deletion time. If non-NULL, the channel has been "deleted" and should not usually be
    #: visible.
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{} ("{}")'.format(self.id, self.title)


class PlaylistQuerySet(PermissionQuerySetMixin, models.QuerySet):
    def annotate_viewable(self, user, name='viewable'):
        """
        Annotate the query set with a boolean indicating if the user can view the item.

        """
        return self.annotate(**{
            name: models.Case(
                models.When(
                    Q(self._permission_condition('view_permission', user) |
                      self._permission_condition('channel__edit_permission', user)),
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def viewable_by_user(self, user):
        """
        Filter the queryset to only those items which can be viewed by the passed Django user.

        """
        return self.filter(Q(self._permission_condition('view_permission', user) |
                             self._permission_condition('channel__edit_permission', user)))

    def annotate_editable(self, user, name='editable'):
        """
        Annotate the query set with a boolean indicating if the user can edit the playlist.

        """
        return self.annotate(**{
            name: models.Case(
                models.When(
                    self._permission_condition('channel__edit_permission', user),
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            ),
        })

    def editable_by_user(self, user):
        """
        Filter the queryset to only those playlists which can be edited by the passed Django user.

        """
        return self.filter(self._permission_condition('channel__edit_permission', user))


class PlaylistManager(models.Manager):
    """
    An object manager for :py:class:`~.Playlist` objects. Accepts an additional named parameter
    *include_deleted* which specifies if the default queryset should include deleted items.

    """
    def __init__(self, *args, include_deleted=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._include_deleted = include_deleted

    def get_queryset(self):
        qs = PlaylistQuerySet(self.model, using=self._db)
        if not self._include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs


class Playlist(models.Model):
    """
    An individual playlist in the media platform.

    """
    #: Object manager. See :py:class:`~.PlaylistManager`. The objects returned by this manager do
    #: not include deleted objects. See :py:attr:\~.objects_including_deleted`.
    objects = PlaylistManager()

    #: Object manager whose objects include the deleted items. This has been separated out into a
    #: separate manager to avoid inadvertently including deleted objects in a query
    objects_including_deleted = PlaylistManager(include_deleted=True)

    #: Primary key
    id = models.CharField(
        max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: Channel which contains playlist
    channel = models.ForeignKey(
        'Channel', help_text='channel containing playlist', on_delete=models.CASCADE,
        related_name='playlist'
    )

    #: Playlist title
    title = models.TextField(help_text='Title of the playlist', blank=False)

    #: Playlist description
    description = models.TextField(help_text='Description of the playlist', blank=True, default='')

    #: :py:class:`~.MediaItem` objects which make up this playlist.
    media_items = pgfields.ArrayField(
        models.CharField(max_length=_TOKEN_LENGTH), blank=True, default=_blank_array,
        help_text='Primary keys of media items in this playlist'
    )

    #: Creation time
    created_at = models.DateTimeField(auto_now_add=True)

    #: Last update time
    updated_at = models.DateTimeField(auto_now=True)

    #: Deletion time. If non-NULL, the channel has been "deleted" and should not usually be
    #: visible.
    deleted_at = models.DateTimeField(null=True, blank=True)

    @cached_property
    def fetched_media_items_in_order(self):
        """Helper method that fetch the playlist's :py:class:`~.MediaItem` objects
        ordering them as defined by media_items."""
        media_items_by_id = {
            item.id: item
            for item in MediaItem.objects.filter(id__in=self.media_items)
                .select_related('jwp')
        }
        return [media_items_by_id[id] for id in self.media_items if id in media_items_by_id]

    def __str__(self):
        return '{} ("{}")'.format(self.id, self.title)


@receiver(post_save, sender=MediaItem)
def _media_item_post_save_handler(*args, sender, instance, created, raw, **kwargs):
    """
    A post_save handler for :py:class:`~.MediaItem` which creates blank view and edit permissions
    if they don't exist.

    """
    # If this is a "raw" update (e.g. from a test fixture) or was not the creation of the item,
    # don't try to create objects.
    if raw or not created:
        return

    if not hasattr(instance, 'view_permission'):
        Permission.objects.create(allows_view_item=instance)


@receiver(post_save, sender=Channel)
def _channel_post_save_handler(*args, sender, instance, created, raw, **kwargs):
    """
    A post_save handler for :py:class:`~.Channel` which creates a blank edit permission if it don't
    exist.

    """
    # If this is a "raw" update (e.g. from a test fixture) or was not the creation of the channel,
    # don't try to create objects.
    if raw or not created:
        return

    if not hasattr(instance, 'edit_permission'):
        Permission.objects.create(allows_edit_channel=instance)


@receiver(post_save, sender=Playlist)
def _playlist_post_save_handler(*args, sender, instance, created, raw, **kwargs):
    """
    A post_save handler for :py:class:`~.Playlist` which creates an IS_PUBLIC permission if it
    doesn't exist.

    """
    # If this is a "raw" update (e.g. from a test fixture) or was not the creation of the playlist,
    # don't try to create objects.
    if raw or not created:
        return

    Permission.objects.get_or_create(allows_view_playlist=instance, is_public=True)


def _lookup_groupids_and_instids_for_user(user):
    """
    Return a tuple containing the list of group groupids and institution instids which the
    specified user is (publicly) a member of. The return value is cached so it is safe to call this
    multiple times.

    """
    # automationlookup.get_person return values are cached
    person = automationlookup.get_person(
        identifier=user.username, scheme=getattr(settings, 'LOOKUP_SCHEME', 'crsid'),
        fetch=['all_groups', 'all_insts']
    )
    # "be liberal in what you accept" - do not assume that all the fields we expect to be
    # present in the result will be
    return (
        [
            group.get('groupid') for group in person.get('groups', [])
            if group.get('groupid') is not None
        ],
        [
            inst.get('instid') for inst in person.get('institutions', [])
            if inst.get('instid') is not None
        ]
    )
