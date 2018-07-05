from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

import smsjwplatform.jwplatform as api
from smsjwplatform.models import CachedResource

from .. import views


class ViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.get_request = self.factory.get('/')
        self.user = get_user_model().objects.create_user(username='test0001')
        self.patch_get_jwplatform_client()
        self.patch_get_person()
        self.client = self.get_jwplatform_client()

    def patch_get_jwplatform_client(self):
        self.get_jwplatform_client_patcher = mock.patch(
            'smsjwplatform.jwplatform.get_jwplatform_client')
        self.get_jwplatform_client = self.get_jwplatform_client_patcher.start()
        self.addCleanup(self.get_jwplatform_client_patcher.stop)

    def patch_get_person(self):
        self.get_person_patcher = mock.patch('automationlookup.get_person')
        self.get_person = self.get_person_patcher.start()
        self.get_person.return_value = {
            'institutions': [{'instid': 'UIS'}],
            'groups': [{'groupid': '12345', 'name': 'uis-members'}]
        }
        self.addCleanup(self.get_person_patcher.stop)


class ProfileViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.ProfileView().as_view()

    def test_anonymous(self):
        """An anonymous user should have is_anonymous set to True."""
        response = self.view(self.get_request)
        self.assertTrue(response.data['is_anonymous'])

    def test_authenticated(self):
        """An anonymous user should have is_anonymous set to False and username set."""
        force_authenticate(self.get_request, user=self.user)
        response = self.view(self.get_request)
        self.assertFalse(response.data['is_anonymous'])
        self.assertEqual(response.data['username'], self.user.username)

    def test_urls(self):
        """The profile should include a login URL."""
        response = self.view(self.get_request)
        self.assertIn('login', response.data['urls'])


class CollectionListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.CollectionListView().as_view()
        self.client.channels.list.return_value = {
            'status': 'ok',
            'channels': CHANNELS_FIXTURE,
            'limit': 10,
            'offset': 0,
            'total': 30,
        }

    def test_basic_list(self):
        """An user should get all SMS channels back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        # We have some results
        self.assertNotEqual(len(response_data['results']), 0)

        # How many results do we expect
        visible_channels = [
            c for c in CHANNELS_FIXTURE
            if c.get('custom', {}).get('sms_collection_id') is not None
        ]

        # How many do we get
        self.assertEqual(len(response_data['results']), len(visible_channels))

    def test_jwplatform_error(self):
        """A JWPlatform error should be reported as a bad gateway error."""
        self.client.channels.list.return_value = {'status': 'error'}
        response = self.view(self.get_request)
        self.assertEqual(response.status_code, 502)

    def test_search(self):
        """A search options should be passed through to the API call."""
        self.view(self.factory.get('/?search=foo'))
        call_args = self.client.channels.list.call_args
        self.assertIsNotNone(call_args)
        self.assertIn('search', call_args[1])
        self.assertEqual(call_args[1]['search'], 'foo')


class MediaListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaListView().as_view()
        for video in VIDEOS_FIXTURE:
            CachedResource.objects.create(type=CachedResource.VIDEO, key=video['key'], data=video)

    def test_basic_list(self):
        """An user should get all SMS media back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        # We have some results
        self.assertNotEqual(len(response_data['results']), 0)

        # How many results do we expect
        visible_videos = [
            v for v in VIDEOS_FIXTURE if (
                v.get('custom', {}).get('sms_media_id') is not None
                and 'WORLD' in v.get('custom', {}).get('sms_acl', '')
            )
        ]

        # How many do we get
        self.assertEqual(len(response_data['results']), len(visible_videos))

    def test_auth_list(self):
        """An authenticated user should get more SMS media back."""
        unauth_response_data = self.view(self.get_request).data

        force_authenticate(self.get_request, user=self.user)
        auth_response_data = self.view(self.get_request).data

        # Authorised users have more results
        self.assertGreater(
            len(auth_response_data['results']), len(unauth_response_data['results']))


class MediaViewTestCase(ViewTestCase):

    def setUp(self):
        super().setUp()
        self.view = views.MediaView().as_view()

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_success(self, mock_from_id):
        """Check that a media item is successfully returned"""
        mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)

        # test
        response = self.view(self.get_request, 'XYZ123')

        mock_from_id.assert_called_with('XYZ123')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['id'], 'mock1')
        self.assertEqual(response.data['title'], 'Mock 1')
        self.assertEqual(response.data['description'], 'Description for mock 1')
        self.assertEqual(response.data['published_at_timestamp'], 1234567)
        self.assertEqual(
            response.data['poster_image_url'], 'https://cdn.jwplayer.com/thumbs/mock1-720.jpg'
        )
        self.assertEqual(response.data['duration'], 54.0)
        self.assertEqual(response.data['media_id'], '1234')
        self.assertTrue(response.data['player_url'].startswith(
            'https://content.jwplatform.com/players/mock1-someplayer.html'
        ))

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_video_not_found(self, mock_from_id):
        """Check that a 404 is returned if not media is found"""
        mock_from_id.side_effect = api.VideoNotFoundError

        # test
        response = self.view(self.get_request, 'XYZ123')

        self.assertEqual(response.status_code, 404)

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_no_access_to_video(self, mock_from_id):
        """Check that a 403 is returned the caller isn't the ACL"""
        mock_from_id.return_value = api.DeliveryVideo(
            {**DELIVERY_VIDEO_FIXTURE, 'sms_acl': 'acl:CAM:'}
        )

        # test
        response = self.view(self.get_request, 'XYZ123')

        self.assertEqual(response.status_code, 403)


CHANNELS_FIXTURE = [
    {
        'key': 'mock1',
        'title': 'Mock 1',
        'description': 'Description for mock 1',
        'custom': {
            'sms_collection_id': 'collection:1234:',
        },
    },
    {
        'key': 'mock2',
        'title': 'Mock 2',
        'description': 'Description for mock 2',
        'custom': {
            'sms_collection_id': 'collection:1235:',
        },
    },
    {
        'key': 'mock3',
        'title': 'Mock 3',
        'description': 'Not a SMS collection',
    },
]


DELIVERY_VIDEO_FIXTURE = {
    'key': 'mock1',
    'title': 'Mock 1',
    'description': 'Description for mock 1',
    'date': 1234567,
    'duration': 54,
    'sms_acl': 'acl:WORLD:',
    'sms_media_id': 'media:1234:',
}


VIDEOS_FIXTURE = [
    {
        'key': 'mock1',
        'title': 'Mock 1',
        'description': 'Description for mock 1',
        'date': 1234567,
        'duration': 54,
        'custom': {
            'sms_media_id': 'media:1234:',
            'sms_acl': 'acl:WORLD:',
        },
    },
    {
        'key': 'mock2',
        'title': 'Mock 2',
        'description': 'Description for mock 2',
        'date': 1234567,
        'duration': 54,
        'custom': {
            'sms_media_id': 'media:1235:',
            'sms_acl': 'acl:WORLD:',
        },
    },
    # See uisautomation/sms2jwplayer#30. There is a video with an odd ACL.
    {
        'key': 'oddacl',
        'title': 'Mock 2',
        'description': 'Description for mock 2',
        'date': 1234567,
        'duration': 54,
        'custom': {
            'sms_media_id': 'media:1235:',
            'sms_acl': "acl:['']:",
        },
    },
    {
        'key': 'mock3',
        'title': 'Mock 3',
        'description': 'Not a SMS collection',
        'date': 1234567,
        'duration': 54,
        'custom': {},
    },
    {
        'key': 'mock4',
        'title': 'Mock 4',
        'description': 'Description for mock 4',
        'date': 1234567,
        'duration': 54,
        'custom': {
            'sms_media_id': 'media:1435:',
            'sms_acl': 'acl:CAM:',
        },
    },
]
