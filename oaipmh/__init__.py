"""
The ``oaipmh`` application adds support for ingesting media items from Opencast's OAI-PMH
repository.

Overview
--------

`OAI-PMH <https://www.openarchives.org/pmh/>`_ is a standard for publishing "metadata" about
objects. Matadata is hosted in OAI-PMH "repositories" which are accessible over the web. There is a
good `primer <https://sickle.readthedocs.io/en/latest/oaipmh.html>`_ on OAI-PMH in the Sickle
documentation.

Our implementation relies on the OAI-PMH repository build into Opencast. Opencast publishes
additional metadata about mediapackages using it's own XML schema. Conventially, these are
published under the "matterhorn" metadata prefix.

Repositories are configured via the :py:class:`oaipmh.models.Repository` model. A repository has
at least a URL and may optionally have some authentication information.

Once configured, new metadata records can be harvested using either the ``oaipmh_harvest``
management command or the :py:class:`oaipmh.tasks.harvest_all_repositories` and
:py:class:`oaipmh.tasks.harvest_repository` Celery tasks.

When new metadata is harvested, a :py:class:`oaipmh.models.Record` object is created for each
record in the repository. Additionally, a :py:class:`oaipmh.models.MatterhornRecord` object is
created for each Opencast media package.

When a new :py:class:`oaipmh.models.MatterhornRecord` object is created, any tracks which match the
:py:class:`oaipmh.records.TRACK_TYPE` type will have :py:class:`oaipmh.models.Track` objects
created. Similarly, :py:class:`oaipmh.models.Series` objects will be created for all Opencast
series which have records.

The :py:class:`oaipmh.models.Series` model has a ``playlist`` field which points to the
:py:class:`mediapackages.models.Playlist` associated with the series. This field has to be set
manually at the moment. When a new :py:class:`oaipmh.models.Track` object is added to the database
and its associated series has a playlist, a new media item is created from the track's content and
added to the playlist. If the series has no associated playlist or if the track is of the wrong
type, no media item is created.

In order to handle cases where, for example, a series gains a playlist after tracks have already
been harvested, there is a "cleanup" task which can be run via either the ``cleanup`` management
command or the :py:class:`oaipmh.tasks.cleanup` Celery task. This task will try to run the various
object creation/media upload jobs which the database assert should be done but which have not. This
is usually only required if the database is changed manually or if there is an error uploading a
media item.

Set up
------

To set up the OAI-PMH harvester, follow the following steps:

1. Create a :py:class:`oaipmh.models.Repository` object in the database representing the OAI-PMH
   repository which should be harvested from.

2. Schedule harvesting either by having the ``oaipmh_harvest`` management command run via a cronjob
   or schedule the :py:class:`oaipmh.tasks.harvest_all_repositories` Celery task. It is recommended
   that this job runs regularly, perhaps every minute. If you want to make sure you never miss any
   metadata updates, one can schedule a "fetch all records" harvest nightly.

3. It is also worth scheduling the ``oaipmh_cleanup`` management command or
   :py:class:`oaipmh.tasks.cleanup` Celery task to run every so often. (E.g. the basic cleanup
   every 5 minutes and the full cleanup nightly.)

4. Optionally, pre-configure a series by creating a :py:class:`oaipmh.models.Series` object for the
   repository. The value for "identifier" can be found in the Opencast admin UI. From the list of
   "series", open the properties for a series. The "UID" at the bottom of the "Metadata" table is
   the value which should be added as an identifier.

5. Run an initial harvest and create a playlist for any series you want syncing.

Permissions
-----------

Permissions on newly created media items are by default empty so that nobody can see the media
items (apart from super users). The default permissions can be set per series in the
:py:class:`oaipmh.models.Series` object.

Note that these permissions are **only** set on initial media creation. After that point,
permissions can be changed as usual and will not be modified further by the harvesting process.
These permissions do not override the usual behaviour that videos are invisible until the backend
has confirmed processing is complete. (E.g. a ``jwpfetch`` has to have run for the JWPlayer
backend.)

Track types
-----------

By default, any track with the type ``presentation/delivery`` will be ingested. If other tracks
need to be added, the ``OAIPMH_TRACK_TYPES`` can be used. It is a list of track types which will be
ingested by the harvest task. If this setting is changed a "fetch all records"-style harvest should
be run via the ``oaipmh_harvest`` management command.

"""
default_app_config = 'oaipmh.apps.Config'
