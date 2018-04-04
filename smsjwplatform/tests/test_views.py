"""
Tests for views.

"""
from contextlib import contextmanager
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase


class EmbedTest(TestCase):

    def test_embed(self):
        """
        Test basic functionality of embed client.

        """
        with patched_client() as jwclient:
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
        with patched_client():
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
        with patched_client():
            # Try to embed an audio stream
            r = self.client.get(
                reverse('smsjwplatform:embed', kwargs={'media_id': 34}) + '?format=audio')
            self.assertEqual(r.status_code, 200)

            # Check that an appropriate URL fragment is in the response
            self.assertIn('players/{}-{}.js'.format(
                'myaudiokey', settings.JWPLATFORM_EMBED_PLAYER_KEY), r.content.decode('utf8'))

    def test_no_permission(self):
        """
        Tests the behaviour when the user's identity (if any) doesn't match the ACL.

        """
        with patched_client() as jwclient:
            jwclient.videos.show.return_value = {'video': {'custom': {'sms_acl': 'acl:USER_mb2174:'}}}
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)
            self.assertTemplateUsed(r, 'smsjwplatform/401.html')
            # a login_url indicates the template will ask the user to login
            self.assertIn("login_url", r.context)

            self.client.force_login(User.objects.create(username='rjw57'))
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)
            self.assertTemplateUsed(r, 'smsjwplatform/401.html')
            # no login_url indicates the template will say the user has no permission
            self.assertNotIn("login_url", r.context)

    def test_no_player(self):
        """
        Test 404 behaviour when no player specified in settings.

        """
        with patched_client():
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
            jwclient.videos.list.return_value = {'status': 'ok', 'videos': []}
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 404)

    def test_wrong_media(self):
        """
        Test 404 behaviour when wrong media returned.

        """
        with patched_client():
            # Embedding fails with wrong media id
            r = self.client.get(reverse('smsjwplatform:embed', kwargs={'media_id': 35}))
            self.assertEqual(r.status_code, 404)


# A response from /videos/list which contains two media objects corresponding to the SMS media
# ID "34".
LIST_RESPONSE_WITH_MEDIA = {
    'status': 'ok',
    'videos': [
        {
            'custom': {'sms_media_id': 'media:34:', 'sms_acl': 'acl:WORLD:'},
            'mediatype': 'audio',
            'key': 'myaudiokey',
        },
        {
            'custom': {'sms_media_id': 'media:34:', 'sms_acl': 'acl:WORLD:'},
            'mediatype': 'video',
            'key': 'myvideokey',
        },
    ],
}


@contextmanager
def patched_client():
    """
    Patch smsjwplatform.jwplatform.get_jwplatform_client to return a MagicMock instance. Yield this
    instance when used as a context manager.

    """
    client = mock.MagicMock()
    # No matter how videos are searched, return two with ID: 34
    client.videos.list.return_value = LIST_RESPONSE_WITH_MEDIA
    # return a media item with a WORLD acl
    client.videos.show.return_value = {'video': LIST_RESPONSE_WITH_MEDIA['videos'][0]}
    get_client = mock.MagicMock()
    get_client.return_value = client
    patcher = mock.patch('smsjwplatform.jwplatform.get_jwplatform_client', get_client)
    patcher.start()
    yield client
    patcher.stop()
