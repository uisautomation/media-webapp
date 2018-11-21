import logging

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from .namespaces import MATTERHORN_NAMESPACE
from .records import ensure_matterhorn_record


LOG = logging.getLogger(__name__)


class Repository(models.Model):
    """
    An OAI-PMH repository.

    """
    class Meta:
        verbose_name_plural = "Repositories"

    url = models.URLField(help_text="Endpoint URL for repository")

    basic_auth_user = models.CharField(
        max_length=255, blank=True,
        help_text="Username for basic auth. If blank, no basic auth is performed."
    )

    basic_auth_password = models.CharField(
        max_length=255, blank=True,
        help_text="Password for basic auth. Only used if basic_auth_user is not blank."
    )

    last_harvested_at = models.DateTimeField(
        null=True, blank=True, default=None,
        help_text="Date and time the last harvest was performed."
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation time")

    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")

    def __str__(self):
        return f'{self.url}'


class MetadataFormat(models.Model):
    """
    Metadata format supported by a repository. There is at least one format for each repository and
    each identifier must be unique within a repository.

    """
    class Meta:
        unique_together = [
            ('repository', 'identifier')
        ]

    repository = models.ForeignKey(
        Repository, on_delete=models.CASCADE, related_name="metadata_formats",
        help_text="Repository these metadata formats apply to"
    )

    identifier = models.CharField(
        max_length=1024, help_text="Name of format. Also known as the 'metadata prefix'"
    )

    namespace = models.CharField(max_length=1024, help_text="XML namespace of format")

    schema = models.URLField(help_text="XML schema of format")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation time")

    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")

    def __str__(self):
        return f'{self.identifier}'


class Record(models.Model):
    """
    A record from an OAI-PMH repository.

    """
    class Meta:
        unique_together = [
            # The identifier, metadata format and datestamp are unique within a repository.
            # https://www.openarchives.org/OAI/openarchivesprotocol.html, §2.5
            ('identifier', 'metadata_format', 'datestamp'),
        ]

    identifier = models.CharField(
        max_length=1024,
        help_text="Unique identifier for this record within the repository"
    )

    datestamp = models.DateTimeField(
        help_text="Datestamp of record as returned from repository"
    )

    # The metadata format also implicitly records which repository this record was harvested from
    metadata_format = models.ForeignKey(
        MetadataFormat, related_name="records", on_delete=models.CASCADE,
        help_text="Metadata prefix for this record"
    )

    xml = models.TextField(
        help_text="Raw record XML as returned by repository"
    )

    harvested_at = models.DateTimeField(
        help_text="When this record was last harvested from the repository"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation time")

    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")

    def __str__(self):
        return f'{self.identifier}'


class MatterhornRecord(models.Model):
    """
    Specialisation of Record used for storing Matterhorn records. We cannot directly use model
    inheritance here since the harvester simply creates Record objects and we create the related
    MatterhornRecord object via a post_save hook. This sort of "post-hoc" object inheritance breaks
    some of Django's assumptions.

    """
    record = models.OneToOneField(
        to=Record, related_name='matterhorn', on_delete=models.CASCADE
    )

    title = models.TextField(blank=True, help_text="Human-readable title")

    description = models.TextField(blank=True, help_text="Human-readable description")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation time")

    updated_at = models.DateTimeField(auto_now=True, help_text="Last update time")

    def __str__(self):
        fields = [self.record.identifier]
        if self.title != '':
            fields.append(f'("{self.title}")')
        return ' '.join(fields)


@receiver(post_save, sender=Record)
def update_matterhorn_record(instance, raw, **kwargs):
    """
    A signal handler which is run when each record is updated to see if an associated
    MatterhornRecord should be created.

    """
    # Never try to do anything if "raw" is set.
    if raw:
        return

    # If this record's metadata is not of interest, do nothing
    if instance.metadata_format.namespace != MATTERHORN_NAMESPACE:
        return

    _, created = ensure_matterhorn_record(instance)
    if created:
        LOG.info('Created new matterhorn record for %s', instance.identifier)
