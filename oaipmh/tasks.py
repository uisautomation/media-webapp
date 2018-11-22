"""
Asynchronous tasks

.. autofunction:: harvest_all_repositories

.. autofunction:: harvest_repository

.. autofunction:: cleanup

"""
import datetime
import logging

from celery import shared_task
from dateutil.parser import parse as parse_date
from django.db import transaction
from django.utils.timezone import now
from lxml.etree import tostring as xml_tostring
from sickle.oaiexceptions import NoRecordsMatch

from .client import client_for_repository
from . import models
from . import timezone

from .namespaces import MATTERHORN_NAMESPACE
from .tracks import ensure_track_media_item as _ensure_track_media_item


LOG = logging.getLogger(__name__)


@shared_task(name='oaipmh_harvest_all_repositories')
def harvest_all_repositories(**harvest_args):
    """
    Harvest records from all configured repositories. Keyword arguments are passed to
    harvest_repository.

    """
    for repository in models.Repository.objects.all():
        try:
            harvest_repository(repository, **harvest_args)
        except Exception as e:
            LOG.error('Error harvesting repository "%s"', repository.url)
            LOG.exception(e)


@shared_task(name='oaipmh_harvest_repository')
@transaction.atomic
def harvest_repository(repository_or_id, fetch_all_records=False):
    """
    Harvest metadata from an individual repository. By default, only records which have changed
    since the last fetch date are updated. The "fetch_all_records" argument can be used to fetch
    all records from the server.

    """
    # Set or retrieve the repository object
    if not isinstance(repository_or_id, models.Repository):
        repository = models.Repository.objects.get(id=repository_or_id)
    else:
        repository = repository_or_id

    LOG.info('Harvesting from "%s"', repository)

    if fetch_all_records:
        LOG.info('Fetching all records')
        fetch_from_datetime = None
    elif repository.last_harvested_at is None:
        LOG.info('No previous harvest.')
        fetch_from_datetime = None
    else:
        LOG.info('Previous harvest at %s', repository.last_harvested_at)

        # Fetch from a time pre-dating the last fetch time to allow for some healthy clock drift
        # and for rounding error.
        fetch_from_datetime = repository.last_harvested_at - datetime.timedelta(seconds=30)

    # Construct a sickle client for this repository
    client = client_for_repository(repository)

    # Update metadata formats from repository
    LOG.info('Updating metadata formats')
    _update_metadata_formats(client, repository)

    # Fetch records
    LOG.info('Fetching records')
    _update_records(client, repository, fetch_from_datetime)


def _update_metadata_formats(client, repository):
    added, updated, fetched = 0, 0, 0

    for metadata_format in client.ListMetadataFormats():
        fetched += 1

        # These fields are the ones that are "sensitive" in that the object is updated if they
        # change.
        format_fields = {
            'namespace': metadata_format.metadataNamespace,
            'schema': metadata_format.schema
        }

        obj, created = models.MetadataFormat.objects.get_or_create(
            repository=repository, identifier=metadata_format.metadataPrefix,
            defaults=format_fields
        )

        if created:
            added += 1
        elif any(getattr(obj, k) != v for k, v in format_fields.items()):
            # The object existed and has some different fields
            for k, v in format_fields.items():
                setattr(obj, k, v)
            obj.save()
            updated += 1

    LOG.info('Fetched %s format(s)', fetched)
    LOG.info('Added %s new format(s)', added)
    LOG.info('Updated %s existing format(s)', updated)


def _update_records(client, repository, fetch_from_datetime):
    added, updated, fetched = 0, 0, 0

    # Record harvest time
    harvest_time = now()

    # Arguments to listRecords verb
    list_records_args = {}

    # If we're asked to fetch from a particular time, add the "from" argument
    if fetch_from_datetime is not None:
        list_records_args['from'] = timezone.datetime_as_utcdatetime(fetch_from_datetime)

    # Fetch records for each metadata format
    for metadata_format in models.MetadataFormat.objects.filter(repository=repository):
        LOG.info('Fetching records for metadata prefix "%s"', metadata_format.identifier)

        try:
            records = client.ListRecords(
                metadataPrefix=metadata_format.identifier, ignore_deleted=True, **list_records_args
            )
        except NoRecordsMatch:
            # It's OK for no records to be returned but OAI-PMH considers this an error.
            LOG.info('No records returned')
            continue

        for record in records:
            fetched += 1

            try:
                # These fields are the ones that are "sensitive" in that the object is updated if
                # they change.
                record_fields = {
                    'datestamp': parse_date(record.header.datestamp),
                    'xml': xml_tostring(record.xml).decode('utf8')
                }

                obj, created = models.Record.objects.get_or_create(
                    identifier=record.header.identifier, metadata_format=metadata_format,
                    defaults={'harvested_at': harvest_time, **record_fields}
                )

                if created:
                    added += 1
                elif any(getattr(obj, k) != v for k, v in record_fields.items()):
                    # The object existed and has some different fields
                    for k, v in record_fields.items():
                        setattr(obj, k, v)
                    obj.harvested_at = harvest_time
                    obj.save()
                    updated += 1
            except Exception as e:
                # Log any exception and carry on
                LOG.exception(e)

    # Update repository harvest time stamp
    repository.last_harvested_at = harvest_time
    repository.save()

    # Log results
    LOG.info('Fetched %s record(s)', fetched)
    LOG.info('Added %s new record(s)', added)
    LOG.info('Updated %s existing record(s)', updated)


@shared_task(name='oaipmh_cleanup')
@transaction.atomic
def cleanup(full=False):
    """
    Perform various cleanup tasks which help to keep the database tidy. This task performs the
    following:

    * Create/update MatterhornRecord objects based on the corresponding Record. (I.e. any changes
      which was missed by the post_save hook.)

    * Create media items for any Track objects which are missing one and whose Series has an
      associated playlist.

    If "full" is True then a "fuller" cleanup is performed which is likely to touch most objects in
    the database.

    Usually these cleanup tasks need not be performed but it is safe to schedule the cleanup task
    nightly to clear up any inconsistencies in the database.

    """
    _create_matterhorn_records(update_all=full)
    _create_media_items_for_tracks()


def _create_matterhorn_records(update_all=False):
    """
    Utility function which will create MatterhornRecord objects for any Record objects which need
    one. Ordinarily, this would not need to be run except that after a database migration of code
    change, the XML for existing record objects will not necessarily be re-parsed. Causing this
    function to be called periodically will help keep the database consistent.

    """
    LOG.info('Creating MatterhornRecord objects')

    # Get a list of all records which need an associated matterhorn record but don't have one at
    # the moment.
    filter_args = {'metadata_format__namespace': MATTERHORN_NAMESPACE}
    if not update_all:
        # If not updating *all* records, only update those which do not have a record already.
        filter_args['matterhorn__isnull'] = True

    for record in models.Record.objects.filter(**filter_args):
        # Call save on the record, will fire the post-save handler to create the new record.
        try:
            record.save()
        except Exception as e:
            LOG.error('Exception when updating record')
            LOG.exception(e)


def _create_media_items_for_tracks():
    """
    Create media items for all tracks which are lacking them but whose associated series has a
    playlist set.

    """
    LOG.info('Creating track media items')

    # Get list of tracks which should have media items created
    tracks = models.Track.objects.filter(
        matterhorn_record__series__playlist__isnull=False,
        media_item__isnull=True
    ).select_related('matterhorn_record__record', 'matterhorn_record__series')

    for track in tracks:
        LOG.info(
            'Creating media item for track "%s" from record "%s"', track.identifier,
            track.matterhorn_record.record.identifier
        )
        try:
            _ensure_track_media_item(track)
        except Exception as e:
            LOG.error('Exception when creating media item')
            LOG.exception(e)


@shared_task(name='oaipmh_ensure_track_media_item')
def ensure_track_media_item(track_or_id):
    """
    Task wrapper for oaipmh.tracks.ensure_track_media_item.

    """
    # Set or retrieve the track object
    if not isinstance(track_or_id, models.Track):
        track = models.Track.objects.get(id=track_or_id)
    else:
        track = track_or_id

    # Call implementation
    _ensure_track_media_item(track)
