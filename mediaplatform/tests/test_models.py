from django.test import TestCase

from .. import models


class MediaItemTest(TestCase):
    fixtures = ['mediaplatform/tests/fixtures/test_data.yaml']

    def test_creation(self):
        """A MediaItem object should be creatable with no field values."""
        models.MediaItem.objects.create()

    def test_no_deleted_in_objects(self):
        """The default queryset used by MediaItem.objects contains no deleted items."""
        self.assertEqual(models.MediaItem.objects.filter(deleted_at__isnull=False).count(), 0)

    def test_deleted_in_objects_including_deleted(self):
        """If we explicitly ask for deleted objects, we get them."""
        self.assertGreater(
            models.MediaItem.objects_including_deleted.filter(deleted_at__isnull=False).count(), 0)


class CollectionTest(TestCase):
    def test_creation(self):
        """A Collection object should be creatable with no field values."""
        models.Collection.objects.create()


class PermissionTest(TestCase):
    def test_creation(self):
        """A Permission object should be creatable with no field values."""
        models.Permission.objects.create()
