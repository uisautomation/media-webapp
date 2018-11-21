"""
Matterhorn record parsing

"""
import logging

from django.conf import settings
from lxml import etree

from . import models
from .namespaces import MATTERHORN_NAMESPACE, OAI_NAMESPACE, MEDIAPACKAGE_NAMESPACE


LOG = logging.getLogger(__name__)


def ensure_matterhorn_record(record):
    """
    Ensure that a MatterhornRecord object exists for the passed Record. Like get_or_create, returns
    an object, created tuple.

    """
    if record.metadata_format.namespace != MATTERHORN_NAMESPACE:
        LOG.info('Not updating record for wrong namespace')
        return

    # Get or create the associated MatterhornRecord
    matterhorn_record, created = models.MatterhornRecord.objects.get_or_create(record=record)
    if created:
        LOG.info('Created matterhorn record for %s', record.identifier)

    # OK, so it's a bit unpleasant that we re-parse the XML here even though sickle will already
    # have parsed it. OTOH, I really like the fact that the parsing of specialised record types is
    # decoupled from creation so I'm living with it for the moment. -- RJW
    root = etree.fromstring(record.xml)

    # lxml requires that all tags have their namespaces be specified. One can do this with
    # something like element.find('{http://alice.local/ns1}foo/{http://bob.local/ns2}bar') but that
    # quickly gets unwieldy. This mapping can be passed to all find() functions to allow namespaces
    # to be specified via short names like they are in XML itself. So, with the namespace
    # configuration below, one can search for a "mediapackage" tag from the media package namespace
    # which is contained within an "metadata" tag from the OAI namespace using the more friendly
    # search path 'oai:metadata/m:mediapackage' rather than having to, e.g. use
    # f'{{{OAI_NAMESPACE}}}metadata/{{{MEDIAPACKAGE_NAMESPACE}}}mediapackage'.
    namespaces = {
        'oai': OAI_NAMESPACE,
        'm': MEDIAPACKAGE_NAMESPACE,
    }

    # Find the media package element
    mediapackage = root.find('./oai:metadata/m:mediapackage', namespaces=namespaces)
    if mediapackage is None:
        raise RuntimeError(f'No media package found in record {record.identifier}')

    # A dictionary which holds attributes to be set on the record.
    attrs = {}

    # Get title/description of package.
    attrs['title'] = mediapackage.findtext('./m:title', namespaces=namespaces) or ''
    attrs['description'] = mediapackage.findtext('./m:description', namespaces=namespaces) or ''

    # Pull out the series and the title of the series
    series_id = mediapackage.findtext('./m:series', namespaces=namespaces) or ''
    series_title = mediapackage.findtext('./m:seriestitle', namespaces=namespaces) or ''

    # Create or update the series, setting it on the record
    series, series_created = models.Series.objects.get_or_create(
        identifier=series_id, repository=record.metadata_format.repository
    )
    if series_created:
        LOG.info('Created new series "%s"', series_id)
    attrs['series'] = series

    # Update any attributes on the series we need to
    series_attrs = {'title': series_title}
    if any(getattr(series, k) != v for k, v in series_attrs.items()):
        for k, v in series_attrs.items():
            setattr(series, k, v)
        LOG.info('Updated metadata for series "%s"', series_id)
        series.save()

    # Get track elements which should turn into media items. Currently we simply look for tracks
    # with the correct type attribute.
    track_types = set(getattr(settings, 'OAIPMH_TRACK_TYPES', ['presentation/delivery']))
    tracks = [
        t for t in mediapackage.findall(f'./m:media/m:track', namespaces=namespaces)
        if t.get('type') in track_types
    ]

    if len(tracks) > 1:
        LOG.warn(
            'Record "%s" has more than one matching track. Choosing first one',
            record.identifier
        )

    for track in tracks[:1]:
        # Create or update track as appropriate.

        # These attributes are "sensitive" in that, if they change, the track object will be
        # updated.
        track_attrs = {
            'url': track.findtext('./m:url', namespaces=namespaces) or '',
            'xml': etree.tostring(track).decode('utf8'),
        }

        track_obj, track_created = models.Track.objects.get_or_create(
            matterhorn_record=matterhorn_record, identifier=track.get('id'),
            defaults=track_attrs
        )
        if track_created:
            LOG.info('Created track "%s"', track_obj.identifier)

        # Update track if necessary
        if any(getattr(track_obj, k) != v for k, v in track_attrs.items()):
            LOG.info('Updating track "%s"', track_obj.identifier)
            for k, v in track_attrs.items():
                setattr(track_obj, k, v)
            track_obj.save()

    # Update record if necessary
    if any(getattr(matterhorn_record, k) != v for k, v in attrs.items()):
        LOG.info('Updating record "%s"', record.identifier)
        for k, v in attrs.items():
            setattr(matterhorn_record, k, v)
        matterhorn_record.save()

    return matterhorn_record, created
