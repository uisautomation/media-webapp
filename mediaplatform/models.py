import secrets

import automationlookup
from django.conf import settings
import django.contrib.postgres.fields as pgfields
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
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


class MediaItemQuerySet(models.QuerySet):
    def viewable_by_user(self, user):
        """
        Filter the queryset to only those items which can be viewed by the passed Django user.

        """
        # Start with the condition that the item must be public
        condition = models.Q(view_permission__is_public=True)

        # If a non-None user was passed and the user is not anonymous, we can add additional ways
        # the item can be viewed
        if user is not None and not user.is_anonymous:
            groupids, instids = _lookup_groupids_and_instids_for_user(user)

            # Irrespective of user groups/institutions, any signed in user can view videos with the
            # is_signed_in permission
            condition |= models.Q(view_permission__is_signed_in=True)

            # The user may also be explicitly mentioned in the list of allowed crsids
            condition |= models.Q(view_permission__crsids__contains=[user.username])

            # The user's lookup groups may overlap with the allowed set
            condition |= models.Q(view_permission__lookup_groups__overlap=groupids)

            # The user's lookup institutions may overlap with the allowed set
            condition |= models.Q(view_permission__lookup_insts__overlap=instids)

        return self.filter(condition)


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


class MediaItem(models.Model):
    """
    An individual media item in the media platform.

    Most fields in this model can store blank values since they are synced from external providers
    who may not have the degree of rigour we want. For the same reason, we have default values for
    most fields.

    """
    VIDEO = 'video'
    AUDIO = 'audio'
    UNKNOWN = 'unknown'
    TYPE_CHOICES = ((VIDEO, 'Video'), (AUDIO, 'Audio'))

    LANGUAGE_CHOICES = sorted(
        ((language.part3, language.name) for language in languages),
        key=lambda choice: choice[1]
    )

    #: Object manager. See :py:class:`~.MediaItemManager`. The objects returned by this manager do
    #: not include deleted objects. See :py:attr:\~.objects_including_deleted`.
    objects = MediaItemManager()

    #: Object manager whose objects include the deleted items. This has been separated out into a
    #: separate manager to avoid inadvertently including deleted objects in a query
    objects_including_deleted = MediaItemManager(include_deleted=True)

    #: Primary key
    id = models.CharField(
            max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: Media item title
    title = models.TextField(help_text='Title of media item', blank=True, default='')

    #: Media item description
    description = models.TextField(blank=True, default='', help_text='Description of media item')

    #: Duration
    duration = models.FloatField(null=True, editable=False, help_text='Duration of video')

    #: Type of media.
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=VIDEO, editable=False,
        help_text='Type of media (video, audio or unknown)')

    #: Publication date
    published_at = models.DateTimeField(null=True, help_text='Date from which video is visible')

    #: Downloadable flag
    downloadable = models.BooleanField(
        default=False,
        help_text='If this item can be viewed, can it also be downloaded?')

    #: ISO 693-3 language code
    language = models.CharField(
        max_length=3, blank=True, default='', choices=LANGUAGE_CHOICES,
        help_text=(
            'ISO 639-3 three letter language code describing majority language used in this item'
        )
    )

    #: Video copyright
    copyright = models.TextField(
        blank=True, default='', help_text='Free text describing Copyright holder')

    #: List of tags for video
    tags = pgfields.ArrayField(models.CharField(max_length=256), default=[],
                               help_text='Tags/keywords for item')

    #: Creation time
    created_at = models.DateTimeField(auto_now_add=True)

    #: Last update time
    updated_at = models.DateTimeField(auto_now=True)

    #: Deletion time. If non-NULL, the item has been "deleted" and should not usually be visible.
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{} ("{}")'.format(self.id, self.title)


class Collection(models.Model):
    """
    A collection of media items.

    Most fields in this model can store blank values since they are synced from external providers
    who may not have the degree of rigour we want. For the same reason, we have default values for
    most fields.

    """
    #: Primary key
    id = models.CharField(
            max_length=_TOKEN_LENGTH, primary_key=True, default=_make_token, editable=False)

    #: Collection title
    title = models.TextField(help_text='Title of collection', blank=True, default='')

    #: Collection description
    description = models.TextField(help_text='Description for collection', blank=True, default='')

    #: List of tags for collection
    tags = pgfields.ArrayField(models.CharField(max_length=256), default=[],
                               help_text='Tags/keywords for item')

    #: :py:class:`~.MediaItem` objects which make up this collection. Postgres does not (currently)
    #: allow array elements to have a foreign key constraint added to them so we need to represent
    #: the links as bare UUIDs. The upshot of this is that code which uses this field needs to
    #: handle the (rare) case that a UUID in the list does not correspond to a current video.
    #: YouTube, as an example, has this problem as well since videos in playlists are sometimes
    #: replaced by a "deleted video" placeholder.
    media_items = pgfields.ArrayField(
        models.UUIDField(), default=[], help_text='Primary keys of media items in this collection')

    #: Creation time
    created_at = models.DateTimeField(auto_now_add=True)

    #: Last update time
    updated_at = models.DateTimeField(auto_now=True)

    #: Deletion time. If non-NULL, the item has been "deleted" and should not usually be visible.
    deleted_at = models.DateTimeField(null=True, blank=True)


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

    #: MediaItem whose edit permission is this object
    allows_edit_item = models.OneToOneField(
        MediaItem, on_delete=models.CASCADE, related_name='edit_permission', editable=False,
        null=True
    )

    #: Collection whose view permission is this object
    allows_view_collection = models.OneToOneField(
        Collection, on_delete=models.CASCADE, related_name='view_permission', editable=False,
        null=True
    )

    #: Collection whose edit permission is this object
    allows_edit_collection = models.OneToOneField(
        Collection, on_delete=models.CASCADE, related_name='edit_permission', editable=False,
        null=True
    )

    #: List of crsids of users with this permission
    crsids = pgfields.ArrayField(models.TextField(), blank=True, default=[])

    #: List of lookup groups which users with this permission belong to
    lookup_groups = pgfields.ArrayField(models.TextField(), blank=True, default=[])

    #: List of lookup institutions which users with this permission belong to
    lookup_insts = pgfields.ArrayField(models.TextField(), blank=True, default=[])

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
    if not hasattr(instance, 'edit_permission'):
        Permission.objects.create(allows_edit_item=instance)


@receiver(post_save, sender=Collection)
def _collection_post_save_handler(*args, sender, instance, created, raw, **kwargs):
    """
    A post_save handler for :py:class:`~.Collection` which creates blank view and edit permissions
    if they don't exist.

    """
    # If this is a "raw" update (e.g. from a test fixture) or was not the creation of the item,
    # don't try to create objects.
    if raw or not created:
        return

    if not hasattr(instance, 'view_permission'):
        Permission.objects.create(allows_view_collection=instance)
    if not hasattr(instance, 'edit_permission'):
        Permission.objects.create(allows_edit_collection=instance)


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
