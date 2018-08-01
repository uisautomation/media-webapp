from unittest import mock

from dateutil import parser as dateparser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

import smsjwplatform.jwplatform as api
import mediaplatform.models as mpmodels

from .. import views


class ViewTestCase(TestCase):
    fixtures = ['api/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        self.factory = APIRequestFactory()
        self.get_request = self.factory.get('/')
        self.user = get_user_model().objects.get(pk=1)
        self.patch_get_jwplatform_client()
        self.patch_get_person()
        self.jwp_client = self.get_jwplatform_client()
        self.non_deleted_media = mpmodels.MediaItem.objects.all()
        self.media_including_deleted = mpmodels.MediaItem.objects_including_deleted.all()
        self.viewable_by_anon = self.non_deleted_media.viewable_by_user(AnonymousUser())
        self.viewable_by_user = self.non_deleted_media.viewable_by_user(self.user)

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
        self.jwp_client.channels.list.return_value = {
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
        self.jwp_client.channels.list.return_value = {'status': 'error'}
        response = self.view(self.get_request)
        self.assertEqual(response.status_code, 502)

    def test_search(self):
        """A search options should be passed through to the API call."""
        self.view(self.factory.get('/?search=foo'))
        call_args = self.jwp_client.channels.list.call_args
        self.assertIsNotNone(call_args)
        self.assertIn('search', call_args[1])
        self.assertEqual(call_args[1]['search'], 'foo')


class MediaListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaListView().as_view()

    def test_basic_list(self):
        """An anonymous user should get expected media back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.viewable_by_anon.count())

        expected_ids = set(o.id for o in self.viewable_by_anon)
        for item in response_data['results']:
            self.assertIn(item['key'], expected_ids)

    def test_auth_list(self):
        """An authenticated user should get expected media back."""
        force_authenticate(self.get_request, user=self.user)
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        # sanity check that the viewable lists differ
        self.assertNotEqual(self.viewable_by_user.count(), self.viewable_by_anon.count())

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.viewable_by_user.count())

        expected_ids = set(o.id for o in self.viewable_by_user)
        for item in response_data['results']:
            self.assertIn(item['key'], expected_ids)


class MediaViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaView().as_view()
        self.dv_from_key_patcher = mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
        self.dv_from_key = self.dv_from_key_patcher.start()
        self.dv_from_key.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        self.addCleanup(self.dv_from_key_patcher.stop)

    def test_success(self):
        """Check that a media item is successfully returned"""
        item = self.non_deleted_media.get(id='populated')

        # test
        response = self.view(self.get_request, pk=item.id)
        self.assertEqual(response.status_code, 200)

        self.dv_from_key.assert_called_with(item.jwp.key)

        self.assertEqual(response.data['key'], item.id)
        self.assertEqual(response.data['name'], item.title)
        self.assertEqual(response.data['description'], item.description)
        self.assertEqual(dateparser.parse(response.data['uploadDate']), item.published_at)
        self.assertIn(
            'https://cdn.jwplayer.com/thumbs/{}-1280.jpg'.format(item.jwp.key),
            response.data['thumbnailUrl']
        )
        self.assertIsNotNone(response.data['duration'])
        self.assertEqual(response.data['legacy']['id'], item.sms.id)
        self.assertTrue(response.data['embedUrl'].startswith(
            'https://content.jwplatform.com/players/{}-someplayer.html'.format(item.jwp.key)
        ))

    def test_video_not_found(self):
        """Check that a 404 is returned if no media is found"""
        response = self.view(self.get_request, pk='this-media-id-does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_deleted_video_not_found(self):
        """Check that a 404 is returned if a deleted media item is asked for."""
        deleted_item = self.media_including_deleted.filter(deleted_at__isnull=False).first()
        response = self.view(self.get_request, pk=deleted_item.id)
        self.assertEqual(response.status_code, 404)

    def test_non_public_videos_not_found_for_anon(self):
        """Check that a 404 is returned if the anonymous user asks for a video it can't see."""
        user_only_items = (
            {o.id for o in self.viewable_by_user} - {o.id for o in self.viewable_by_anon}
        )
        self.assertGreater(len(user_only_items), 0)

        for id in user_only_items:
            response = self.view(self.get_request, pk=id)
            self.assertEqual(response.status_code, 404)

    def test_non_public_videos_found_for_user(self):
        """Check that a 404 is *not* returned if the user asks for a video it can."""
        force_authenticate(self.get_request, user=self.user)
        for obj in self.viewable_by_user:
            response = self.view(self.get_request, pk=obj.id)
            self.assertEqual(response.status_code, 200)


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
