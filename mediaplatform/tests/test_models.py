from django.test import TestCase

from .. import models


class MediaItemTest(TestCase):
    def test_creation(self):
        """A MediaItem object should be creatable with no field values."""
        models.MediaItem.objects.create()


class CollectionTest(TestCase):
    def test_creation(self):
        """A Collection object should be creatable with no field values."""
        models.Collection.objects.create()


class PermissionTest(TestCase):
    def test_creation(self):
        """A Permission object should be creatable with no field values."""
        models.Permission.objects.create()
