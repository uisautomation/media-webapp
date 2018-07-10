from django.db import models


class MediaItem(models.Model):
    """
    A media item hosted on the legacy SMS.

    """

    #: SMS media id
    id = models.BigIntegerField(primary_key=True, editable=False, help_text='Legacy SMS media id')

    #: Corresponding :py:class:`mediaplatform.MediaItem`. Accessible from the
    #: :py:class:`mediaplatform.MediaItem` model via the ``sms`` field. This can be NULL if there
    #: is no corresponding media item hosted by the Media Platform.
    item = models.OneToOneField('mediaplatform.MediaItem', related_name='sms',
                                on_delete=models.SET_NULL, null=True)

    #: The last updated at time from the legacy SMS. Used to determine which items need updating.
    last_updated_at = models.DateTimeField(help_text='Last updated at time from SMS')


class Collection(models.Model):
    """
    A collection hosted on the legacy SMS.

    """

    #: SMS collection id
    id = models.BigIntegerField(primary_key=True, editable=False,
                                help_text='Legacy SMS collection id')

    #: Corresponding :py:class:`mediaplatform.Collection`. Accessible from the
    #: :py:class:`mediaplatform.Collection` model via the ``sms`` field. This can be NULL if there
    #: is no corresponding collection hosted by the Media Platform.
    collection = models.OneToOneField('mediaplatform.Collection', related_name='sms',
                                      on_delete=models.SET_NULL, null=True)

    #: The last updated at time from the legacy SMS. Used to determine which collections need
    #: updating.
    last_updated_at = models.DateTimeField(help_text='Last updated at time from SMS')
