import json

from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction, connection
from psycopg2.extras import execute_batch


class CachedResourceManager(models.Manager):
    """
    A models.Manager subclass which includes a method for updating the resource cache.

    See the documentation for :py:class:`.CachedResource` for an example of usage.

    """
    @transaction.atomic
    def _set_resources(self, type, resources):
        """
        Helper function which updates the cached resources and marks resources as deleted if no
        longer present.

        :param type: type of resource to be cached
        :type type: str
        :param resources: iterable of (key, dict) pairs representing the resources
        :type resources: iterable

        Iterates over all of the dicts in *resources* adding or updating corresponding
        :py:class:`~.CachedResource` models as it goes. After all resources have been added, any
        resources of the specified type which have not been created or updated are deleted from the
        cache.

        This is all run inside an atomic block. Note that these blocks can be nested so calls to
        this function can themselves be within an atomic block.

        [1] https://docs.djangoproject.com/en/2.0/topics/db/transactions/#django.db.transaction.atomic

        """  # noqa: E501
        allowed_types = {name for name, _ in CachedResource.TYPE_CHOICES}
        if type not in allowed_types:
            raise ValueError(f'Unknown type: {type}')

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
                    INSERT INTO smsjwplatform_cachedresource (
                        key, data, type, updated_at, created_at, deleted_at
                    ) VALUES (
                        %(key)s, %(data)s, %(type)s,
                        STATEMENT_TIMESTAMP(), STATEMENT_TIMESTAMP(), NULL
                    )
                    ON CONFLICT (key) DO
                        UPDATE SET
                            data = %(data)s, type = %(type)s,
                            updated_at = STATEMENT_TIMESTAMP(), deleted_at = NULL
                        WHERE smsjwplatform_cachedresource.key = %(key)s
                    RETURNING
                        smsjwplatform_cachedresource.key AS key
                )
                INSERT INTO inserted_or_updated_keys (key) SELECT key FROM insert_result
            ''', (
                {'key': key, 'data': json.dumps(data), 'type': str(type)}
                for key, data in iter(resources)
            ))

            cursor.execute('''
                UPDATE
                    smsjwplatform_cachedresource
                SET
                    deleted_at = STATEMENT_TIMESTAMP()
                WHERE
                    key NOT IN (SELECT key from inserted_or_updated_keys)
                    AND type = %(type)s
            ''', {'type': type})

            cursor.execute('''DROP TABLE inserted_or_updated_keys''')


class CachedResourceTypeManager(CachedResourceManager):
    """
    A models.Manager subclass which, together with :py:class:`CachedResource`, restricts the base
    query set to the *non-deleted* cached resources of a particular type.

    See the documentation for :py:class:`.CachedResource` for an example of usage.

    """
    def __init__(self, type):
        super().__init__()
        self._type = type

    def get_queryset(self):
        return super().get_queryset().filter(type=self._type, deleted_at=None)

    def set_resources(self, resources):
        """
        Helper function which updates the cached resources and marks resources as deleted if no
        longer present. Operates only on the resource types relating to this object manager.

        :param resources: iterable of (key, dict) pairs representing the resources
        :type resources: iterable

        Iterates over all of the dicts in *resources* adding or updating corresponding
        :py:class:`~.CachedResource` models as it goes. After all resources have been added, any
        resources of the specified type which have not been created or updated are deleted from the
        cache.

        This is all run inside an atomic block. Note that these blocks can be nested so calls to
        this function can themselves be within an atomic block.

        [1] https://docs.djangoproject.com/en/2.0/topics/db/transactions/#django.db.transaction.atomic

        """  # noqa: E501
        return self._set_resources(self._type, resources)


class CachedResource(models.Model):
    """
    A cache of a JWPlatform resource.

    This model should be queried by way of the various type-specific helpers. For example, to
    filter videos by title:

    .. code::

        CachedResource.videos.filter(data__title='some title')

    Do not insert values directly, instead use the
    :py:meth:`~.CachedResourceTypeManager.set_resources`` method to update the cached resources
    atomically:

    .. code::

        CachedResource.videos.set_resources((video['key'], video) for video in fetch_videos())

    N.B. Since we use Postgres-specific field types (JSONB), this model requires that Postgres be
    the database.

    """
    #: video resource type
    VIDEO = 'video'

    TYPE_CHOICES = (
        (VIDEO, 'Video'),
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

    #: Convenience manager instance whose base queryset is all the non-deleted videos
    videos = CachedResourceTypeManager(VIDEO)

    #: Since we add an object manager, we need to explicitly add back the default one
    objects = models.Manager()

    class Meta:
        indexes = [
            # A GIN index over the data field to allow efficient indexing of the composite type.
            # https://www.postgresql.org/docs/current/static/gin-intro.html
            GinIndex(fields=['data']),

            # A simple index over the type which is a common field used for filtering the initial
            # set of resources
            models.Index(fields=['type']),
        ]
