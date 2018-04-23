"""
Tests for views.

"""
import copy
from contextlib import contextmanager
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
import requests

import smsjwplatform.jwplatform as api

from .. import redirect


class EmbedTest(TestCase):

    def test_embed(self):
        """
        Test basic functionality of embed client.

        """
        with patched_client() as jwclient:
            # Try to embed a video
            r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 34}))
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
                reverse('legacysms:embed', kwargs={'media_id': 34}) + '?format=video')
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
                reverse('legacysms:embed', kwargs={'media_id': 34}) + '?format=audio')
            self.assertEqual(r.status_code, 200)

            # Check that an appropriate URL fragment is in the response
            self.assertIn('players/{}-{}.js'.format(
                'myaudiokey', settings.JWPLATFORM_EMBED_PLAYER_KEY), r.content.decode('utf8'))

    def test_no_permission(self):
        """
        Tests the behaviour when the user's identity (if any) doesn't match the ACL.

        """
        with patched_client() as jwclient:
            jwclient.videos.show.return_value = {
                'video': {'custom': {'sms_acl': 'acl:USER_mb2174:'}}
            }
            r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)
            self.assertTemplateUsed(r, 'smsjwplatform/401.html')
            # a login_url indicates the template will ask the user to login
            self.assertIn("login_url", r.context)

            self.client.force_login(User.objects.create(username='rjw57'))
            r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 200)
            self.assertTemplateUsed(r, 'smsjwplatform/401.html')
            # no login_url indicates the template will say the user has no permission
            self.assertNotIn("login_url", r.context)

    def test_no_media(self):
        """
        Test redirect behaviour when no media returned.

        """
        with patched_client() as jwclient:
            # No matter how videos are searched, return none
            jwclient.videos.list.return_value = {'status': 'ok', 'videos': []}
            r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 34}))
            self.assertRedirects(r, redirect.media_embed(34)['Location'],
                                 fetch_redirect_response=False)

    def test_wrong_media(self):
        """
        Test redirect behaviour when wrong media returned.

        """
        with patched_client():
            # Embedding fails with wrong media id
            r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 35}))
            self.assertRedirects(r, redirect.media_embed(35)['Location'],
                                 fetch_redirect_response=False)

    def test_rss_media(self):
        """
        Test RSS media feed.

        """
        # We mock time.time() here since URL signing uses the current time as an input and we want
        # to ensure that we generate the same signature.
        with patched_client(), mock.patch('time.time', return_value=12345):
            # Try to embed a video
            r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 34}))

            # Should be redirect to RSS URL.
            expected_url = api.pd_api_url('/v2/media/myvideokey', format='mrss')
            self.assertRedirects(r, expected_url, fetch_redirect_response=False)

    def test_rss_media_redirect(self):
        """
        Test RSS media feed redirects if media item not found.

        """
        with mock.patch('smsjwplatform.jwplatform.key_for_media_id',
                        side_effect=api.VideoNotFoundError()):
            # Try to embed a video
            r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 34}))

            # Should be redirect
            self.assertRedirects(r, redirect.media_rss(34)['Location'],
                                 fetch_redirect_response=False)


class DownloadTests(TestCase):
    """
    Test media download functionality.

    """

    def setUp(self):
        # Patch the key_for_media_id call
        self.key_for_media_id_patcher = mock.patch('smsjwplatform.jwplatform.key_for_media_id')

        # Patch the requests library
        self.requests_session_patcher = mock.patch('legacysms.views.DEFAULT_REQUESTS_SESSION')

        self.key_for_media_id = self.key_for_media_id_patcher.start()
        self.requests_session = self.requests_session_patcher.start()

    def tearDown(self):
        # Stop patching
        self.key_for_media_id_patcher.stop()
        self.requests_session_patcher.stop()

    def test_basic_functionality(self):
        """Basic redirection functionality works."""
        self.key_for_media_id.return_value = 'video-key'
        self.requests_session.get.return_value.json.return_value = MEDIA_INFO

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertRedirects(r, 'http://media.invalid/2.mp4', fetch_redirect_response=False)

    def test_passes_video_key_to_jwp(self):
        """The correct video key used to get video info."""
        self.key_for_media_id.return_value = 'video-key'

        self.client.get(reverse('legacysms:download_media',
                                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.requests_session.get.assert_called_once_with(
            api.pd_api_url(f'/v2/media/video-key', format='json'), timeout=5
        )

    def test_redirects_if_not_found(self):
        """Redirects to legacy SMS if video is not present."""
        self.key_for_media_id.side_effect = api.VideoNotFoundError()

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

    def test_bad_gateway_if_timeout(self):
        """If request times out, a bad gateway error is returned."""
        self.key_for_media_id.return_value = 'video-key'
        self.requests_session.get.side_effect = requests.Timeout()

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_bad_gateway_if_upstream_error(self):
        """If request to JWPlayer gives HTTP error, a bad gateway error is returned."""
        self.key_for_media_id.return_value = 'video-key'
        self.requests_session.get.return_value.raise_for_status.side_effect = requests.HTTPError()

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_bad_gateway_if_bad_json(self):
        """If request to JWPlayer gives un-parseable JSON, a bad gateway error is returned."""
        self.key_for_media_id.return_value = 'video-key'
        self.requests_session.get.return_value.json.side_effect = Exception()

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_redirects_if_no_playlist(self):
        """Redirects to legacy SMS if there is no playlist or an empty playlist."""
        self.key_for_media_id.return_value = 'video-key'

        # No playlist
        self.requests_session.get.return_value.json.return_value = {}
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

        # Empty playlist
        self.requests_session.get.return_value.json.return_value = {'playlist': []}
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

    def test_redirects_if_no_sources(self):
        """Redirects to legacy SMS if there are no sources."""
        self.key_for_media_id.return_value = 'video-key'

        # No sources
        self.requests_session.get.return_value.json.return_value = {'playlist': [{}]}
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

        # Empty sources
        self.requests_session.get.return_value.json.return_value = {'playlist': [{'sources': []}]}
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

    def test_404_if_bad_extension(self):
        """404 is returned if an unknown extension is given"""
        self.key_for_media_id.return_value = 'video-key'
        self.requests_session.get.return_value.json.return_value = MEDIA_INFO

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension':
                                            'not-a-video'}))

        self.assertEqual(r.status_code, 404)

    def test_redirects_if_no_file(self):
        """Redirects to legacy SMS if the source has no file set."""
        self.key_for_media_id.return_value = 'video-key'

        media_info = copy.deepcopy(MEDIA_INFO)
        media_info['playlist'][0]['sources'] = [
            {'width': 1280, 'height': 720, 'type': 'video/mp4'}
        ]

        self.requests_session.get.return_value.json.return_value = media_info
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)


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
