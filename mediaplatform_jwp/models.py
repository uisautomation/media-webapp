from django.db import models


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
    #: an integer field rather than a datetime filed because JWP uses timestamps and we should
    #: store the same value to make sure we compare apples to apples.
    updated = models.BigIntegerField(help_text='Last updated timestamp', editable=False)
