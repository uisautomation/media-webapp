"""
Tests for views.

"""
from contextlib import contextmanager
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from mediaplatform_jwp.models import CachedResource
from mediaplatform import models as mpmodels
from mediaplatform_jwp import sync

from .. import models
from .. import redirect


class TestCaseWithFixtures(TestCase):
    fixtures = ['legacysms/tests/fixtures/objects.yaml']

    def setUp(self):
        for video in VIDEOS_FIXTURE:
            CachedResource.objects.create(type=CachedResource.VIDEO, key=video['key'], data=video)
        sync.update_related_models_from_cache()

        get_person_patcher = mock.patch('automationlookup.get_person')
        self.get_person = get_person_patcher.start()
        self.addCleanup(get_person_patcher.stop)
        self.get_person.return_value = {'institutions': [], 'groups': []}


class EmbedTest(TestCaseWithFixtures):
    def test_embed(self):
        """
        Test basic functionality of embed client.

        """
        # Try to embed a video
        r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 34}))
        item = mpmodels.MediaItem.objects.get(sms__id=34)
        self.assertRedirects(
            r, reverse('api:media_embed', kwargs={'pk': item.id}),
            fetch_redirect_response=False)

    def test_no_media(self):
        """
        Test 404 behaviour when no media is in local cache.

        """
        r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 12345}))
        self.assertEqual(r.status_code, 404)

    def test_wrong_media(self):
        """
        Test 404 behaviour when wrong media returned.

        """
        # Embedding fails with wrong media id
        r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 35}))
        self.assertEqual(r.status_code, 404)


class RSSMediaTestCase(TestCaseWithFixtures):
    def test_basic_functionality(self):
        """
        Test RSS media feed.

        """
        item = mpmodels.MediaItem.objects.get(sms__id=34)
        r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': item.sms.id}))
        expected_url = reverse('ui:media_item_rss', kwargs={'pk': item.id})
        self.assertRedirects(r, expected_url, fetch_redirect_response=False)

    def test_no_permission(self):
        """
        RSS media 404s if the user doesn't have access.

        """
        item = mpmodels.MediaItem.objects.get(sms__id=34)
        item.view_permission.reset()
        item.view_permission.save()
        r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': item.sms.id}))
        self.assertEqual(r.status_code, 404)

    def test_no_match(self):
        """
        RSS media feed 404s if no media found.

        """
        r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 78654}))
        self.assertEqual(r.status_code, 404)


class DownloadTests(TestCaseWithFixtures):
    """
    Test media download functionality.

    """

    def test_basic_functionality(self):
        """Basic redirection functionality works."""
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        item = mpmodels.MediaItem.objects.get(sms__id=34)

        self.assertRedirects(
            r, reverse('api:media_source', kwargs={'pk': item.id}),
            fetch_redirect_response=False)

    def test_404_if_not_found(self):
        """Returns a 404 response if video is not present."""
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 3456, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertEqual(r.status_code, 404)


class MediaPageTest(TestCaseWithFixtures):
    def test_basic_redirect(self):
        """
        Test basic functionality of embed client.

        """
        r = self.client.get(reverse('legacysms:media', kwargs={'media_id': 34}))
        item = mpmodels.MediaItem.objects.get(sms__id=34)
        self.assertRedirects(r, reverse('ui:media_item', kwargs={'pk': item.id}))

    def test_no_permission(self):
        """
        Tests the behaviour when the user's identity (if any) doesn't match the ACL. The behaviour
        should be as if the media does not exist.

        """
        item = mpmodels.MediaItem.objects.get(sms__id=34)
        item.view_permission.reset()
        item.view_permission.save()

        r = self.client.get(reverse('legacysms:media', kwargs={'media_id': 34}))
        self.assertRedirects(r, redirect.media_page(34)['Location'],
                             fetch_redirect_response=False)

        self.client.force_login(User.objects.create(username='spqr1'))
        r = self.client.get(reverse('legacysms:media', kwargs={'media_id': 34}))
        self.assertRedirects(r, redirect.media_page(34)['Location'],
                             fetch_redirect_response=False)

    def test_no_media(self):
        """
        Test redirect behaviour when no media is in local cache.

        """
        r = self.client.get(reverse('legacysms:media', kwargs={'media_id': 12345}))
        self.assertRedirects(r, redirect.media_page(12345)['Location'],
                             fetch_redirect_response=False)


class RSSCollectionTestCase(TestCaseWithFixtures):
    def setUp(self):
        self.collection = models.Collection.objects.get(id=1234)

    def test_basic_functionality(self):
        """
        Test RSS collection feed.

        """
        r = self.client.get(reverse(
            'legacysms:rss_collection', kwargs={'collection_id': self.collection.id}
        ))
        expected_url = reverse('ui:playlist_rss', kwargs={'pk': self.collection.playlist.id})
        self.assertRedirects(r, expected_url, fetch_redirect_response=False)

    def test_no_permission(self):
        """
        RSS collection 404s if the user doesn't have access.

        """
        self.collection.playlist.view_permission.reset()
        self.collection.playlist.view_permission.save()
        r = self.client.get(reverse(
            'legacysms:rss_collection', kwargs={'collection_id': self.collection.id}
        ))
        self.assertEqual(r.status_code, 404)

    def test_no_match(self):
        """
        RSS collection feed 404s if no collection found.

        """
        r = self.client.get(reverse(
            'legacysms:rss_collection', kwargs={'collection_id': 123456}
        ))
        self.assertEqual(r.status_code, 404)


# Two media objects corresponding to the SMS media ID "34".
VIDEOS_FIXTURE = [
    {
        'custom': {'sms_media_id': 'media:34:', 'sms_acl': 'acl:WORLD:'},
        'mediatype': 'audio',
        'key': 'myaudiokey',
        'status': 'ready',
    },
    {
        'custom': {'sms_media_id': 'media:34:', 'sms_acl': 'acl:WORLD:'},
        'mediatype': 'video',
        'key': 'myvideokey',
        'status': 'ready',
    },
]

# A media information resource fixture.
MEDIA_INFO = {
    'playlist': [
        {
            'sources': [
                {
                    'width': 160, 'height': 120, 'type': 'video/mp4',
                    'file': 'http://media.invalid/1.mp4',
                },
                {
                    'width': 720, 'height': 576, 'type': 'video/mp4',
                    'file': 'http://media.invalid/2.mp4',
                },
                {
                    'type': 'audio/mp4', 'file': 'http://media.invalid/1.m4a',
                },
                {
                    'width': 720, 'height': 576, 'type': 'application/vnd.apple.mpegurl',
                    'file': 'http://media.invalid/1.m3u8',
                },
            ]
        }
    ],
}


@contextmanager
def patched_client():
    """
    Patch mediaplatform_jwp.api.delivery.get_jwplatform_client to return a
    MagicMock instance.
    Yield this instance when used as a context manager.

    """
    client = mock.MagicMock()
    get_client = mock.MagicMock()
    get_client.return_value = client
    patcher = mock.patch('mediaplatform_jwp.api.delivery.get_jwplatform_client',
                         get_client)
    patcher.start()
    yield client
    patcher.stop()
