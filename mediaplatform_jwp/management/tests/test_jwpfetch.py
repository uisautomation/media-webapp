from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from mediaplatform_jwp.models import CachedResource


class JWPFetchTest(TestCase):
    """
    Tests for the jwpfetch management command.

    """
    VIDEOS_FIXTURE = [
        {'title': 'video A', 'key': 'A'},
        {'title': 'video B', 'key': 'B'},
    ]

    def setUp(self):
        self.jwp_client = mock.MagicMock()

        get_jwplatform_client_patcher = mock.patch(
            'mediaplatform_jwp.jwplatform.get_jwplatform_client', return_value=self.jwp_client
        )
        get_jwplatform_client_patcher.start()
        self.addCleanup(get_jwplatform_client_patcher.stop)

    def test_basic_functionality(self):
        """
        Command calls jwplatform API and caches result.

        """
        def videos(result_offset=0, **kwargs):
            return {'videos': self.VIDEOS_FIXTURE[result_offset:]}

        self.assertEqual(CachedResource.videos.count(), 0)
        self.jwp_client.videos.list.side_effect = videos
        call_command('jwpfetch')
        self.assertEqual(CachedResource.videos.count(), len(self.VIDEOS_FIXTURE))
        for video in self.VIDEOS_FIXTURE:
            self.assertEqual(
                CachedResource.videos.get(key=video['key']).data.get('title'), video['title']
            )

    def test_deletes_missing_resources(self):
        """
        Command deletes any missing resources

        """
        def videos1(result_offset=0, **kwargs):
            return {'videos': self.VIDEOS_FIXTURE[result_offset:]}

        def videos2(result_offset=0, **kwargs):
            return {'videos': self.VIDEOS_FIXTURE[1:][result_offset:]}

        self.assertEqual(CachedResource.videos.count(), 0)
        self.jwp_client.videos.list.side_effect = videos1
        call_command('jwpfetch')
        self.assertEqual(CachedResource.videos.count(), len(self.VIDEOS_FIXTURE))
        self.jwp_client.videos.list.side_effect = videos2
        call_command('jwpfetch')
        self.assertEqual(CachedResource.videos.count(), len(self.VIDEOS_FIXTURE) - 1)
