"""
Tests for views.

"""
import copy
from contextlib import contextmanager
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
import requests

import mediaplatform_jwp.api.delivery as api
from mediaplatform_jwp.models import CachedResource
from mediaplatform import models as mpmodels
from mediaplatform_jwp import sync

from .. import redirect
from .. import views


class TestCaseWithFixtures(TestCase):
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
        Test redirect behaviour when no media is in local cache.

        """
        r = self.client.get(reverse('legacysms:embed', kwargs={'media_id': 12345}))
        self.assertRedirects(r, redirect.media_embed(12345)['Location'],
                             fetch_redirect_response=False)

    def test_wrong_media(self):
        """
        Test redirect behaviour when wrong media returned.

        """
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
        with mock.patch('time.time', return_value=12345):
            # Try to embed a video
            r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 34}))

            # Should be redirect to RSS URL.
            expected_url = api.pd_api_url('/v2/media/myvideokey', format='mrss')
            self.assertRedirects(r, expected_url, fetch_redirect_response=False)

    def test_rss_no_permission(self):
        """
        Tests the behaviour when the user's identity (if any) doesn't match the ACL for the RSS
        feed.

        """
        with mock.patch('mediaplatform_jwp.api.delivery.Video.from_media_id'
                        ) as from_media_id:
            from_media_id.return_value = api.Video({
                'key': 'video-key',
                'custom': {
                    'sms_acl': 'acl:USER_mb2174:',
                    'sms_media_id': 'media:34:',
                }
            })
            self.assertEqual(api.Video.from_media_id(34).acl, ['USER_mb2174'])

            r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 403)

            self.client.force_login(User.objects.create(username='spqr1'))
            r = self.client.get(reverse('legacysms:rss_media', kwargs={'media_id': 34}))
            self.assertEqual(r.status_code, 403)

    def test_rss_media_redirect(self):
        """
        Test RSS media feed redirects if media item not found.

        """
        with mock.patch('mediaplatform_jwp.api.delivery.Video.from_media_id',
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
        # Patch the video_from_media_id call
        self.video_from_media_id_patcher = mock.patch(
            'mediaplatform_jwp.api.delivery.Video.from_media_id')

        # Patch the requests library
        self.requests_session_patcher = mock.patch('legacysms.views.DEFAULT_REQUESTS_SESSION')

        self.video_from_media_id = self.video_from_media_id_patcher.start()
        self.requests_session = self.requests_session_patcher.start()

        # Video.from_media_id() by default returns a mock Video resource
        self.mock_video = api.Video({'key': 'video-key'})
        self.video_from_media_id.return_value = self.mock_video

    def tearDown(self):
        # Stop patching
        self.video_from_media_id_patcher.stop()
        self.requests_session_patcher.stop()

    def test_basic_functionality(self):
        """Basic redirection functionality works."""
        self.requests_session.get.return_value.json.return_value = MEDIA_INFO

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertRedirects(r, 'http://media.invalid/2.mp4', fetch_redirect_response=False)

    def test_passes_video_key_to_jwp(self):
        """The correct video key used to get video info."""
        with mock.patch('time.time', return_value=12345):
            self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

            self.requests_session.get.assert_called_once_with(
                api.pd_api_url(f'/v2/media/video-key', format='json'), timeout=5
            )

    def test_redirects_if_not_found(self):
        """Redirects to legacy SMS if video is not present."""
        self.video_from_media_id.side_effect = api.VideoNotFoundError()

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

    def test_bad_gateway_if_timeout(self):
        """If request times out, a bad gateway error is returned."""
        self.requests_session.get.side_effect = requests.Timeout()

        # Check that a warning is also logged
        with self.assertLogs(views.LOG, 'WARNING'):
            r = self.client.get(reverse(
                'legacysms:download_media',
                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_bad_gateway_if_upstream_error(self):
        """If request to JWPlayer gives HTTP error, a bad gateway error is returned."""
        self.requests_session.get.return_value.raise_for_status.side_effect = requests.HTTPError()

        # Check that a warning is also logged
        with self.assertLogs(views.LOG, 'WARNING'):
            r = self.client.get(reverse(
                'legacysms:download_media',
                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_bad_gateway_if_bad_json(self):
        """If request to JWPlayer gives un-parseable JSON, a bad gateway error is returned."""
        self.requests_session.get.return_value.json.side_effect = Exception()

        # Check that a warning is also logged
        with self.assertLogs(views.LOG, 'WARNING'):
            r = self.client.get(reverse(
                'legacysms:download_media',
                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))

        self.assertEqual(r.status_code, 502)

    def test_redirects_if_no_playlist(self):
        """Redirects to legacy SMS if there is no playlist or an empty playlist."""
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
        self.requests_session.get.return_value.json.return_value = MEDIA_INFO

        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension':
                                            'not-a-video'}))

        self.assertEqual(r.status_code, 404)

    def test_redirects_if_no_file(self):
        """Redirects to legacy SMS if the source has no file set."""
        media_info = copy.deepcopy(MEDIA_INFO)
        media_info['playlist'][0]['sources'] = [
            {'width': 1280, 'height': 720, 'type': 'video/mp4'}
        ]

        self.requests_session.get.return_value.json.return_value = media_info
        r = self.client.get(reverse('legacysms:download_media',
                                    kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
        self.assertRedirects(r, redirect.media_download(34, 56, 'mp4')['Location'],
                             fetch_redirect_response=False)

    def test_no_permission(self):
        """
        Tests the behaviour when the user's identity (if any) doesn't match the ACL.

        """
        with mock.patch('mediaplatform_jwp.api.delivery.Video.from_media_id'
                        ) as from_media_id:
            from_media_id.return_value = api.Video({
                'key': 'video-key',
                'custom': {
                    'sms_acl': 'acl:USER_mb2174:',
                    'sms_media_id': 'media:34:',
                }
            })
            self.assertEqual(api.Video.from_media_id(34).acl, ['USER_mb2174'])

            r = self.client.get(reverse(
                'legacysms:download_media',
                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
            self.assertEqual(r.status_code, 403)

            self.client.force_login(User.objects.create(username='spqr1'))
            r = self.client.get(reverse(
                'legacysms:download_media',
                kwargs={'media_id': 34, 'clip_id': 56, 'extension': 'mp4'}))
            self.assertEqual(r.status_code, 403)


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


# Two media objects corresponding to the SMS media ID "34".
VIDEOS_FIXTURE = [
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
