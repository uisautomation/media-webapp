import datetime
from unittest import mock

from dateutil import parser as dateparser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

import smsjwplatform.jwplatform as api
import mediaplatform.models as mpmodels

from . import create_stats_table, delete_stats_table, add_stat
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
        self.channels = mpmodels.Channel.objects.all()
        self.channels_including_deleted = mpmodels.Channel.objects_including_deleted.all()

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


class MediaItemListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemListView().as_view()
        self.channel = mpmodels.Channel.objects.get(id='channel1')
        self.channel.edit_permission.reset()
        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()

    def test_basic_list(self):
        """An anonymous user should get expected media back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.viewable_by_anon.count())

        expected_ids = set(o.id for o in self.viewable_by_anon)
        for item in response_data['results']:
            self.assertIn(item['id'], expected_ids)

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
            self.assertIn(item['id'], expected_ids)

    def test_create(self):
        """Basic creation of a media item succeeds."""
        request = self.factory.post('/', {'title': 'foo', 'channelId': self.channel.id})
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)
        new_item = mpmodels.MediaItem.objects.get(id=response.data['id'])
        self.assertEqual(new_item.channel.id, self.channel.id)
        self.assertEqual(new_item.title, 'foo')

    def test_create_requires_channel(self):
        """Creation requires channel id."""
        request = self.factory.post('/', {'title': 'foo'})
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_requires_channel_user_can_edit(self):
        """Creation requires channel id for channel the user can edit."""
        self.channel.edit_permission.reset()
        self.channel.edit_permission.save()
        request = self.factory.post('/', {'title': 'foo', 'channelId': self.channel.id})
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 400)


class MediaItemViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemView().as_view()
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

        self.assertEqual(response.data['id'], item.id)
        self.assertEqual(response.data['title'], item.title)
        self.assertEqual(response.data['description'], item.description)
        self.assertEqual(dateparser.parse(response.data['publishedAt']), item.published_at)
        self.assertIn(
            'https://cdn.jwplayer.com/thumbs/{}-640.jpg'.format(item.jwp.key),
            response.data['posterImageUrl']
        )
        self.assertIsNotNone(response.data['duration'])
        self.assertTrue(response.data['links']['embedUrl'].startswith(
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

    def test_success_if_jw_item_not_yet_available(self):
        """Check that the get still succeeds, even tho the JW api throws a VideoNotFoundError"""
        self.dv_from_key.side_effect = api.VideoNotFoundError
        item = self.non_deleted_media.get(id='populated')

        # test
        response = self.view(self.get_request, pk=item.id)
        self.assertEqual(response.status_code, 200)
        # sources cannot be generated and so are set as []
        self.assertEqual(response.data['sources'], [])

    def test_id_immutable(self):
        self.assert_field_immutable('id')

    def test_title_mutable(self):
        self.assert_field_mutable('title')

    def test_downloadable_mutable(self):
        self.assert_field_mutable('downloadable', True)
        self.assert_field_mutable('downloadable', False)

    def test_language_mutable(self):
        self.assert_field_mutable('language', 'elx')

    def test_copyright_mutable(self):
        self.assert_field_mutable('copyright')

    def test_tags_mutable(self):
        self.assert_field_mutable('tags', ['a', 'b', 'c'])

    def test_published_at_mutable(self):
        item = self.non_deleted_media.get(id='populated')
        new_date = item.published_at + datetime.timedelta(seconds=123456789)
        self.assert_field_mutable('publishedAt', new_date.isoformat(), 'published_at', new_date)

    def test_description_mutable(self):
        self.assert_field_mutable('description')

    def test_duration_immutable(self):
        self.assert_field_immutable('duration', 9876)

    def test_type_immutable(self):
        self.assert_field_immutable('type')

    def test_created_at_immutable(self):
        self.assert_field_immutable('createdAt', '2018-08-06T15:29:45.003231Z', 'created_at')

    def test_update(self):
        """Basic update of a media item succeeds."""
        item = self.non_deleted_media.get(id='populated')
        item.channel.edit_permission.crsids.append(self.user.username)
        item.channel.edit_permission.save()
        new_title = item.title + '---with-change'
        request = self.factory.patch('/', {'title': new_title})
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 200)
        new_item = mpmodels.MediaItem.objects.get(id=item.id)
        self.assertEqual(new_item.title, new_title)

    def test_update_channel(self):
        """Cannot change the channel of a media item, even if user has all the right edit
        permissions."""
        item = self.non_deleted_media.get(id='populated')
        item.channel.edit_permission.crsids.append(self.user.username)
        item.channel.edit_permission.save()
        new_channel = mpmodels.Channel.objects.create(title='new channel')
        new_channel.edit_permission.crsids.append(self.user.username)
        new_channel.edit_permission.save()
        request = self.factory.patch('/', {'channelId': new_channel.id})
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 400)

    def assert_field_mutable(
            self, field_name, new_value='testvalue', model_field_name=None, expected_value=None):
        expected_value = expected_value or new_value
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        item = self.non_deleted_media.get(id='populated')
        item.channel.edit_permission.crsids.append(self.user.username)
        item.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 403)

        force_authenticate(request, user=self.user)
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            getattr(self.non_deleted_media.get(id='populated'), model_field_name), expected_value)

    def assert_field_immutable(self, field_name, new_value='test value', model_field_name=None):
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        item = self.non_deleted_media.get(id='populated')
        item.channel.edit_permission.crsids.append(self.user.username)
        item.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 403)

        # Authorised request should have no effect
        original_value = getattr(item, model_field_name)
        self.assertNotEqual(original_value, new_value)
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=item.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            getattr(self.non_deleted_media.get(id='populated'), model_field_name), original_value)


class UploadEndpointTestCase(ViewTestCase):
    fixtures = ['api/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        super().setUp()
        self.view = views.MediaItemUploadView().as_view()
        self.item = mpmodels.MediaItem.objects.get(id='populated')

        # Reset any permissions on the item
        self.item.view_permission.reset()
        self.item.view_permission.save()
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()

    def test_needs_view_permission(self):
        """Upload endpoint should 404 if user doesn't have view permission."""
        response = self.get_for_item()
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.user)
        response = self.get_for_item()
        self.assertEqual(response.status_code, 404)

    def test_needs_edit_permission(self):
        """If user has view but not edit permission, endpoint should deny permission."""
        self.add_view_permission()
        self.client.force_login(self.user)
        response = self.get_for_item()
        self.assertEqual(response.status_code, 403)

    def test_allows_view_and_edit_permission(self):
        """If user has view *and* edit permission, endpoint should succeed."""
        self.client.force_login(self.user)
        self.add_view_permission()
        self.add_edit_permission()
        response = self.get_for_item()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['url'], self.item.upload_endpoint.url)
        self.assertEqual(
            dateparser.parse(body['expires_at']),
            self.item.upload_endpoint.expires_at
        )

    def test_create_upload_endpoint(self):
        """PUT-ing endpoint creates a new upload endpoint."""
        self.client.force_login(self.user)
        self.add_view_permission()
        self.add_edit_permission()

        with mock.patch('mediaplatform_jwp.management.create_upload_endpoint') as mock_create:
            response = self.put_for_item()

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        item = mock_create.call_args[0][0]
        self.assertEqual(item.id, self.item.id)

    def get_for_item(self, **kwargs):
        return self.client.get(reverse('api:media_upload', kwargs={'pk': self.item.pk}), **kwargs)

    def put_for_item(self, **kwargs):
        return self.client.put(reverse('api:media_upload', kwargs={'pk': self.item.pk}), **kwargs)

    def add_view_permission(self):
        self.item.view_permission.crsids.append(self.user.username)
        self.item.view_permission.save()

    def add_edit_permission(self):
        self.item.channel.edit_permission.crsids.append(self.user.username)
        self.item.channel.edit_permission.save()


class MediaItemAnalyticsViewCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        create_stats_table()
        self.addCleanup(delete_stats_table)

    def test_success(self):
        """Check that analytics for a media item is returned"""
        item = self.non_deleted_media.get(id='populated')
        media_id = item.sms.id
        add_stat(day=datetime.date(2018, 5, 17), num_hits=3, media_id=media_id)
        add_stat(day=datetime.date(2018, 3, 22), num_hits=4, media_id=media_id)

        # test
        response = views.MediaItemAnalyticsView().as_view()(self.get_request, pk=item.id)

        self.assertEqual(response.status_code, 200)

        results = response.data['results']

        self.assertEqual(results[0]['date'], '2018-05-17')
        self.assertEqual(results[0]['views'], 3)
        self.assertEqual(results[1]['date'], '2018-03-22')
        self.assertEqual(results[1]['views'], 4)

    def test_no_legacy_sms(self):
        """
        Check that no analytics are returned if a media item doesn't have a legacysms.MediaItem
        """
        item = self.non_deleted_media.get(id='a')

        # test
        response = views.MediaItemAnalyticsView().as_view()(self.get_request, pk=item.id)

        self.assertEqual(response.status_code, 200)

        results = response.data['results']

        self.assertEqual(len(results), 0)


class ChannelListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.ChannelListView().as_view()

    def test_basic_list(self):
        """An anonymous user should get expected channels back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.channels.count())

        expected_ids = set(o.id for o in self.channels)
        for item in response_data['results']:
            self.assertIn(item['id'], expected_ids)


class ChannelViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.ChannelView().as_view()
        # A suitable test channel
        self.channel = self.channels.get(id='channel1')

    def test_success(self):
        """Check that a channel is successfully returned"""
        response = self.view(self.get_request, pk=self.channel.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.channel.id)
        self.assertEqual(response.data['title'], self.channel.title)
        self.assertEqual(response.data['owningLookupInst'], self.channel.owning_lookup_inst)

    def test_not_found(self):
        """Check that a 404 is returned if no channel is found"""
        response = self.view(self.get_request, pk='this-channel-id-does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_deleted_not_found(self):
        """Check that a 404 is returned if a deleted channel item is asked for."""
        deleted_item = self.channels_including_deleted.filter(deleted_at__isnull=False).first()
        self.assertIsNotNone(deleted_item)
        response = self.view(self.get_request, pk=deleted_item.id)
        self.assertEqual(response.status_code, 404)

    def test_id_immutable(self):
        self.assert_field_immutable('id')

    def test_title_mutable(self):
        self.assert_field_mutable('title')

    def test_description_mutable(self):
        self.assert_field_mutable('description')

    def test_owning_lookup_inst_mutable(self):
        self.assert_field_mutable('owningLookupInst', 'ENG', 'owning_lookup_inst')

    def test_created_at_immutable(self):
        self.assert_field_immutable('createdAt', '2018-08-06T15:29:45.003231Z', 'created_at')

    def assert_field_mutable(
            self, field_name, new_value='testvalue', model_field_name=None, expected_value=None):
        expected_value = expected_value or new_value
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=self.channel.id)
        self.assertEqual(response.status_code, 403)

        force_authenticate(request, user=self.user)
        response = self.view(request, pk=self.channel.id)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            getattr(self.channels.get(id=self.channel.id), model_field_name), expected_value)

    def assert_field_immutable(self, field_name, new_value='test value', model_field_name=None):
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=self.channel.id)
        self.assertEqual(response.status_code, 403)

        # Authorised request should have no effect
        original_value = getattr(self.channel, model_field_name)
        self.assertNotEqual(original_value, new_value)
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=self.channel.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            getattr(self.channels.get(id=self.channel.id), model_field_name), original_value)


DELIVERY_VIDEO_FIXTURE = {
    'key': 'mock1',
    'title': 'Mock 1',
    'description': 'Description for mock 1',
    'date': 1234567,
    'duration': 54,
    'sms_acl': 'acl:WORLD:',
    'sms_media_id': 'media:1234:',
}
