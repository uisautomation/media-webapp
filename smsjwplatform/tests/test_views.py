"""
Tests for views.

"""
from contextlib import contextmanager
from unittest import mock

from django.conf import settings
from django.urls import reverse
from django.test import TestCase


class EmbedTest(TestCase):
    # A response from /videos/list which contains two media objects corresponding to the SMS media
    # ID "34".
    LIST_RESPONSE_WITH_MEDIA = {
        'status': 'ok',
        'videos': [
            {
                'custom': {'sms_media_id': 'media:34:'},
                'mediatype': 'audio',
                'key': 'myaudiokey',
            },
            {
                'custom': {'sms_media_id': 'media:34:'},
                'mediatype': 'video',
                'key': 'myvideokey',
            },
        ],
    }

    # A response from /videos/list which has no videos found.
    LIST_RESPONSE_WITH_NOTHING = {'status': 'ok', 'videos': []}

    def test_embed(self):
        """
        Test basic functionality of embed client.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return two with ID: 34
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_MEDIA

            # Try to embed a video
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)

            # Check that the search endpoint was called
            jwclient.videos.list.assert_called()

            # Check that an appropriate URL fragment is in the response
            self.assertIn('players/{}-{}.js'.format(
                'myvideokey', settings.JWPLATFORM_EMBED_PLAYER_KEY), r.content.decode('utf8'))

    def test_video_embed(self):
        """
        Test basic functionality of embed client with an explicit video embed.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return two with ID: 34
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_MEDIA

            # Try to embed a video
            r = self.client.get(
                reverse('smsjwplatform:embed', kwargs={'media_id': 34}) + '?format=video')
            self.assertEqual(r.status_code, 200)

            # Check that an appropriate URL fragment is in the response
            self.assertIn('players/{}-{}.js'.format(
                'myvideokey', settings.JWPLATFORM_EMBED_PLAYER_KEY), r.content.decode('utf8'))

    def test_audio_embed(self):
        """
        Test basic functionality of embed client with an explicit audio embed.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return two with ID: 34
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_MEDIA

            # Try to embed an audio stream
            r = self.client.get(
                reverse('smsjwplatform:embed', kwargs={'media_id': 34}) + '?format=audio')
            self.assertEqual(r.status_code, 200)

            # Check that an appropriate URL fragment is in the response
            self.assertIn('players/{}-{}.js'.format(
                'myaudiokey', settings.JWPLATFORM_EMBED_PLAYER_KEY), r.content.decode('utf8'))

    def test_no_player(self):
        """
        Test 404 behaviour when no player specified in settings.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return two with ID: 34
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_MEDIA

            # Embedding works with setting ...
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)

            # ... and not without
            with self.settings(JWPLATFORM_EMBED_PLAYER_KEY=''):
                r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
                self.assertEqual(r.status_code, 404)

    def test_no_media(self):
        """
        Test 404 behaviour when no media returned.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return none
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_NOTHING
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 404)

    def test_wrong_media(self):
        """
        Test 404 behaviour when wrong media returned.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return two with ID: 34
            jwclient.videos.list.return_value = self.LIST_RESPONSE_WITH_MEDIA

            # Embedding fails with wrong media id
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 35}))
            self.assertEqual(r.status_code, 404)


@contextmanager
def patched_client():
    """
    Patch smsjwplatform.jwplatform.get_jwplatform_client to return a MagicMock instance. Yield this
    instance when used as a context manager.

    """
    client = mock.MagicMock()
    get_client = mock.MagicMock()
    get_client.return_value = client
    patcher = mock.patch('smsjwplatform.jwplatform.get_jwplatform_client', get_client)
    patcher.start()
    yield client
    patcher.stop()
