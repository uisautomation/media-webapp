import random
from django.test import TestCase

from .. import models


class CachedResourceTest(TestCase):
    def setUp(self):
        # A base query set which returns all non-deletes cached videos
        self.videos = models.CachedResource.videos

        # A base query set which returns *all* videos, even the deleted ones
        self.all_videos = models.CachedResource.objects.filter(type=models.CachedResource.VIDEO)

    def test_empty_iterable(self):
        """Cache should be updatable with empty iterable."""
        self.videos.set_resources([])
        # There should be nothing in the cache
        self.assertEqual(self.videos.count(), 0)

    def test_simple_use(self):
        """Simple use of the cache should succeed."""
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'y': 7})
        ])

        # We should now be able to query these values
        self.assertEqual(self.videos.count(), 2)
        self.assertEqual(self.videos.filter(data__x=5).first().key, 'foo')

    def test_expiry(self):
        """If a resource disappears, it should disappear from the cache."""
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'y': 7})
        ])
        self.assertEqual(self.videos.count(), 2)
        self.videos.set_resources([('foo', {'x': 6})])
        self.assertEqual(self.videos.count(), 1)
        self.assertEqual(self.videos.filter(data__x=6).first().key, 'foo')
        self.assertEqual(self.videos.filter(data__x=5).count(), 0)

    def test_updated_at(self):
        """If a value is updated, the updated_at timestamp should be after created_at."""
        self.videos.set_resources([('foo', {'x': 5})])
        self.videos.set_resources([('foo', {'x': 5})])
        obj = self.videos.get(key='foo')
        self.assertGreater(obj.updated_at, obj.created_at)

    def test_iterable_resources(self):
        """update_resource_cache() should accept an iterable."""
        def resources():
            yield 'foo', {'x': 5}
            yield 'bar', {'x': 7}

        self.assertEqual(self.videos.count(), 0)
        self.videos.set_resources(resources())
        self.assertEqual(self.videos.count(), 2)

    def test_duplicate_keys(self):
        """If duplicate keys are in the resource iterable, the last one wins."""
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'x': 6}), ('foo', {'x': 7})
        ])
        obj = self.videos.get(key='foo')
        self.assertEqual(obj.data['x'], 7)

    def test_many_resources(self):
        """Adding many resources should be possible without taking an age."""
        def resources(count):
            # Generate the indices in random order
            for index in random.sample(range(count), k=count):
                yield f'resource_{index}', {'index': index}
        # Stress test the database. If there is a performance regression, we'll notice it when
        # running the tests. Add 10,000 resources then remove 5,000 of them.
        self.videos.set_resources(resources(10000))
        self.videos.set_resources(resources(5000))
        self.assertEqual(self.videos.count(), 5000)

    def test_soft_delete(self):
        """If a resource disappears, it should disappear from the cache but remain in the database
        with a non-NULL deleted_at time."""
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'y': 7})
        ])
        self.assertEqual(self.videos.count(), 2)
        self.videos.set_resources([('foo', {'x': 6})])
        self.assertEqual(self.videos.count(), 1)
        self.assertEqual(self.all_videos.count(), 2)
        o = self.all_videos.get(key='bar')
        self.assertIsNotNone(o.deleted_at)

    def test_reinsertion(self):
        """If a resource disappears and re-appears, the deleted_at field should be None."""
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'y': 7})
        ])
        self.videos.set_resources([('foo', {'x': 6})])
        self.videos.set_resources([
            ('foo', {'x': 5}), ('bar', {'y': 7})
        ])
        self.assertEqual(self.videos.count(), 2)
        self.assertEqual(self.all_videos.count(), 2)
        o = self.all_videos.get(key='bar')
        self.assertIsNone(o.deleted_at)
