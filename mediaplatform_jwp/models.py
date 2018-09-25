import json
import logging

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction, connection
from django.utils.functional import cached_property
from psycopg2.extras import execute_batch

import mediaplatform.models as mpmodels
from mediaplatform_jwp.api import delivery as jwplatform

LOG = logging.getLogger(__name__)


class CachedResourceTypeManager(models.Manager):
    """
    A models.Manager subclass which restricts the base query set to the *non-deleted* cached
    resources of a particular type.

    """
    def __init__(self, type):
        super().__init__()
        self._type = type

    def get_queryset(self):
        return super().get_queryset().filter(type=self._type, deleted_at=None)


class CachedResource(models.Model):
    """
    A cache of a JWPlatform resource.

    This model should be queried by way of the various type-specific helpers. For example, to
    filter videos by title:

    .. code::

        CachedResource.videos.filter(data__title='some title')

    Do not insert values directly, instead use the :py:func:`~.set_videos`` method to update the
    cached resources atomically:

    .. code::

        set_resources((video['key'], video) for video in fetch_videos())

    N.B. Since we use Postgres-specific field types (JSONB), this model requires that Postgres be
    the database.

    """
    #: video resource type
    VIDEO = 'video'

    #: channel resource type
    CHANNEL = 'channel'

    TYPE_CHOICES = (
        (VIDEO, 'Video'),
        (CHANNEL, 'Channel'),
    )

    key = models.CharField(
        max_length=255, unique=True, primary_key=True,
        help_text=('A unique textual key for this resource. E.g. for videos, this can be the '
                   'JWPlatform video key'),
    )

    data = JSONField(
        help_text='The resource data itself',
    )

    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES,
        help_text='The JWPlatform resource type cached in this model',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='The date and time at which this cached resource was first created'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='The date and time at which this cached resource was last updated'
    )

    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None,
        help_text='The date and time at which this cached resource was deleted',
    )

    #: Since we add an object manager, we need to explicitly add back the default one
    objects = models.Manager()

    #: Convenience manager instance whose base queryset is all the non-deleted videos
    videos = CachedResourceTypeManager(VIDEO)

    #: Convenience manager instance whose base queryset is all the non-deleted channels
    channels = CachedResourceTypeManager(CHANNEL)

    class Meta:
        indexes = [
            # A GIN index over the data field to allow efficient indexing of the composite type.
            # https://www.postgresql.org/docs/current/static/gin-intro.html
            GinIndex(fields=['data']),

            # A simple index over the type which is a common field used for filtering the initial
            # set of resources
            models.Index(fields=['type']),
        ]


@transaction.atomic
def set_resources(resources, resource_type):
    """
    Helper function which updates the cached resources and marks resources as deleted if no
    longer present.

    :param resources: iterable of dicts representing the JWPlatform resources
    :type resources: iterable
    :param resource_type: type of JWPlatform resource (e.g. "video")
    :type resource_type: str

    Iterates over all of the dicts in *resources* adding or updating corresponding
    :py:class:`~.CachedResource` models as it goes. After all resources have been added, any
    resources of the specified type which have not been created or updated are deleted from the
    cache.

    This is all run inside an atomic block. Note that these blocks can be nested so calls to
    this function can themselves be within an atomic block.

    [1] https://docs.djangoproject.com/en/2.0/topics/db/transactions/#django.db.transaction.atomic

    """
    # OK, I need to hold my hand up to this being a horrible, brittle HACK but I couldn't
    # determine a clean way to do this with the stock Django ORM. We bypass the ORM entirely
    # and roll our own SQL. The general idea is to, atomically,
    #
    # 1. Create a temporary table to hold all the keys for the resources we inserted/updated in
    #    the cache.
    #
    # 2. Insert/update ("upsert") the resources using PostgreSQL's INSERT ... ON CONFLICT
    #    support. If we insert a new row, created_at and updated_at are set to the statement
    #    timestamp but if an existing row is updated, only the updated_at timestamp is
    #    modified. Along the way, we record the keys of the resources which have been
    #    "upserted" in the temporary table.
    #
    # 3. Mark all the resources of the appropriate type as "deleted" if their key is not in the
    #    temporary table.
    #
    # 4. Drop the temporary table.
    #
    # This approach lets us send the list of new resources to the database *once* and then lets
    # the database sort out evicting/deleting resources from the cache if they weren't inserted
    # in this transaction. We could do much of this with the ORM but the native
    # update_or_create() method would involve a database round trip for each resource which
    # quickly adds up if there are 10,000 of them.
    #
    # Django currently does not support upsert natively in the ORM. A "better" alternative to
    # rolling our own SQL is to use the .on_conflict() support in django-postgres-extra[1] but
    # that requires using an entirely different Postgres backend. Using django-postgres-extra
    # also introduces another dependency as a very low-level component which it'd be hard to
    # migrate from if it becomes abandoned.
    #
    # [1] http://django-postgres-extra.readthedocs.io/manager/#conflict-handling

    with connection.cursor() as cursor:
        # A table to hold the list of inserted or updated keys
        cursor.execute('''
            CREATE TEMPORARY TABLE inserted_or_updated_keys (key TEXT)
        ''')

        # Using execute_batch is many times faster than executemany
        # http://initd.org/psycopg/docs/extras.html#fast-exec
        #
        # There is an argument as to what "now" function we should use here, especially as the
        # test suite runs everything within one transaction so using TRANSACTION_TIMESTAMP()
        # won't actually give any different values when we run testes.
        #
        # We use STATEMENT_TIMESTAMP() as a compromise.
        #
        # The downside of STATEMENT_TIMESTAMP() is that execute_batch() will batch calls so the
        # various ..._at timestamps may differ slightly for a given cache update. OTOH, I don't
        # think anyone will really care about the ..._at timestamps down to that sort of
        # resolution. Given that assumption, I will no doubt be proved wrong when a future data
        # analyst berates us when they analyse our database dumps and find out that the
        # timestamps have a little bit of non-deterministic noise.
        #
        # [1] https://www.postgresql.org/docs/9.1/static/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT  # noqa: E501
        execute_batch(cursor, '''
            WITH
                insert_result
            AS (
                INSERT INTO mediaplatform_jwp_cachedresource (
                    key, data, type, updated_at, created_at, deleted_at
                ) VALUES (
                    %(key)s, %(data)s, %(type)s,
                    STATEMENT_TIMESTAMP(), STATEMENT_TIMESTAMP(), NULL
                )
                ON CONFLICT (key) DO
                    UPDATE SET
                        data = %(data)s, type = %(type)s,
                        updated_at = STATEMENT_TIMESTAMP(), deleted_at = NULL
                    WHERE mediaplatform_jwp_cachedresource.key = %(key)s
                RETURNING
                    mediaplatform_jwp_cachedresource.key AS key
            )
            INSERT INTO inserted_or_updated_keys (key) SELECT key FROM insert_result
        ''', (
            {'key': data['key'], 'data': json.dumps(data), 'type': resource_type}
            for data in iter(resources)
        ))

        cursor.execute('''
            UPDATE
                mediaplatform_jwp_cachedresource
            SET
                deleted_at = STATEMENT_TIMESTAMP()
            WHERE
                key NOT IN (SELECT key from inserted_or_updated_keys)
                AND type = %(type)s
        ''', {'type': resource_type})

        cursor.execute('''DROP TABLE inserted_or_updated_keys''')


class Video(models.Model):
    """
    A JWPlatform video resource.

    """

    #: JWPlatform video key
    key = models.CharField(primary_key=True, max_length=64, editable=False)

    #: Corresponding :py:class:`mediaplatform.MediaItem`. Accessible from the
    #: :py:class:`mediaplatform.MediaItem` model via the ``jwp`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    item = models.OneToOneField('mediaplatform.MediaItem', related_name='jwp',
                                on_delete=models.SET_NULL, null=True, editable=False)

    #: The updated timestamp from JWPlatform. Used to determine which items need updating. This is
    #: an integer field rather than a datetime field because JWP uses timestamps and we should
    #: store the same value to make sure we compare apples to apples.
    updated = models.BigIntegerField(help_text='Last updated timestamp', editable=False)

    #: Cached resource instance associated with this video.
    resource = models.OneToOneField(
        CachedResource, on_delete=models.CASCADE, related_name='video')

    def get_sources(self):
        """
        Uses the JWP fetch API to retrieve a list of :py:class:`mediaplatform.MediaItem.Source`
        instances for each source associated with the media item. Ignores the ``downloadable``
        attribute of the item.

        """
        try:
            video = jwplatform.DeliveryVideo.from_key(self.key)
        except jwplatform.VideoNotFoundError as e:
            # this can occur if the video is still transcoding - better to set the sources to none
            # than fail completely
            LOG.warning("unable to generate download sources as the JW video is not yet available")
            return []

        return [
            mpmodels.MediaItem.Source(
                mime_type=source.get('type'), url=source.get('file'),
                width=source.get('width'), height=source.get('height'),
                item=self.item,
            )
            for source in video.get('sources', [])
        ]

    #: A property which calls get_sources and caches the result.
    sources = cached_property(get_sources, name='sources')

    def embed_url(self, format='html'):
        """
        Return a URL with an embed view of a :py:class:`mediaplatform.MediaItem`. Returns ``None``
        if there is no JWP video associated with the item.
        """
        return jwplatform.player_embed_url(
            self.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, format=format
        )


class Channel(models.Model):
    """
    A JWPlatform channel resource.

    """

    #: JWPlatform channel key
    key = models.CharField(primary_key=True, max_length=64, editable=False)

    #: Corresponding :py:class:`mediaplatform.Channel`. Accessible from the
    #: :py:class:`mediaplatform.Channel` model via the ``jwp`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    channel = models.OneToOneField('mediaplatform.Channel', related_name='jwp',
                                   on_delete=models.SET_NULL, null=True, editable=False)

    #: The updated timestamp from JWPlatform. Used to determine which items need updating. This is
    #: an integer field rather than a datetime field because JWP uses timestamps and we should
    #: store the same value to make sure we compare apples to apples.
    updated = models.BigIntegerField(help_text='Last updated timestamp', editable=False)

    #: Cached resource instance associated with this channel.
    resource = models.OneToOneField(
        CachedResource, on_delete=models.CASCADE, related_name='channel')
