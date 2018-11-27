import datetime
from unittest import mock

from dateutil import parser as dateparser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate

import mediaplatform_jwp.api.delivery as api
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
        self.playlists = mpmodels.Playlist.objects.all()
        self.playlists_visibile_by_anon = (self.playlists.viewable_by_user(AnonymousUser()))
        self.playlists_visibile_by_user = (self.playlists.viewable_by_user(self.user))
        self.playlists_including_deleted = mpmodels.Playlist.objects_including_deleted.all()

        # An unused billing account.
        self.unused_billing_account = mpmodels.BillingAccount.objects.get(id='bacct_nu')

    def patch_get_jwplatform_client(self):
        self.get_jwplatform_client_patcher = mock.patch(
            'mediaplatform_jwp.api.delivery.get_jwplatform_client')
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
        self.get_person.return_value = {
            'displayName': 'Test User',
            'attributes': [
                {
                    'scheme': 'jpegPhoto',
                    'binaryData': 'xxxxx',
                },
            ],
        }

    def test_anonymous(self):
        """An anonymous user should have is_anonymous set to True."""
        response = self.view(self.get_request)
        self.assertTrue(response.data['isAnonymous'])

    def test_authenticated(self):
        """A non-anonymous user should have is_anonymous set to False and username set."""
        force_authenticate(self.get_request, user=self.user)
        response = self.view(self.get_request)
        self.assertFalse(response.data['isAnonymous'])
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['displayName'], self.get_person.return_value['displayName'])
        self.assertIn('xxxx', response.data['avatarImageUrl'])

    def test_token_authenticated(self):
        """A token-authenticated user should get expected media back."""
        token = Token.objects.create(user=self.user)
        token_get_request = self.factory.get('/', HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.view(token_get_request)
        self.assertFalse(response.data['isAnonymous'])
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['displayName'], self.get_person.return_value['displayName'])
        self.assertIn('xxxx', response.data['avatarImageUrl'])

    def test_authenticated_with_no_photo(self):
        """A non-anonymous user with no photo has no avatarImageUrl."""
        force_authenticate(self.get_request, user=self.user)
        del self.get_person.return_value['attributes'][:]
        response = self.view(self.get_request)
        self.assertFalse(response.data['isAnonymous'])
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['displayName'], self.get_person.return_value['displayName'])
        self.assertIsNone(response.data['avatarImageUrl'])

    def test_anonymous_channels(self):
        """An anonymous user should have no editable channels"""
        response = self.view(self.get_request)
        channels = mpmodels.Channel.objects.all().editable_by_user(self.user)
        self.assertFalse(channels.exists())
        self.assertEqual(response.data['channels'], [])

    def test_authenticated_channels(self):
        """An authenticated user should get their channels back."""
        billing_account = self.channels[0].billing_account
        c1 = mpmodels.Channel.objects.create(title='c1', billing_account=billing_account)
        c1.edit_permission.reset()
        c1.edit_permission.save()
        c2 = mpmodels.Channel.objects.create(title='c2', billing_account=billing_account)
        c2.edit_permission.crsids.append(self.user.username)
        c2.edit_permission.save()

        expected_channels = mpmodels.Channel.objects.all().editable_by_user(self.user)
        self.assertTrue(expected_channels.exists())

        expected_ids = set(c.id for c in expected_channels)
        force_authenticate(self.get_request, user=self.user)
        response = self.view(self.get_request)
        received_ids = set(c['id'] for c in response.data['channels'])

        self.assertEqual(expected_ids, received_ids)


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

    def test_basic_playlist_filter(self):
        """Filtering by playlist works."""
        playlist = self.playlists.get(id='public')
        playlist.channel.edit_permission.reset()
        playlist.channel.edit_permission.save()
        playlist.media_items.extend(
            item.id for item in
            mpmodels.MediaItem.objects.all()
            .viewable_by_user(self.user)[:1]
        )
        playlist.save()

        self.assertTrue(
            mpmodels.Playlist.objects.all().viewable_by_user(self.user)
            .filter(id=playlist.id).exists()
        )

        request = self.factory.get('/?playlist=' + playlist.id)
        force_authenticate(request, user=self.user)

        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        received_ids = set(item['id'] for item in response.data['results'])
        expected_ids = set(
            item.id for item in
            mpmodels.MediaItem.objects.all()
            .viewable_by_user(self.user)
            .filter(id__in=playlist.media_items)
        )
        self.assertNotEqual(expected_ids, set())
        self.assertEqual(received_ids, expected_ids)

    def test_non_viewable_playlist_filter(self):
        # Filtering returns no results if playlist has no view permission
        playlist = self.playlists.get(id='public')
        playlist.channel.edit_permission.reset()
        playlist.channel.edit_permission.save()
        playlist.view_permission.reset()
        playlist.view_permission.save()
        playlist.media_items.extend(
            item.id for item in
            mpmodels.MediaItem.objects.all()
            .viewable_by_user(self.user)[:1]
        )
        playlist.save()

        self.assertFalse(
            mpmodels.Playlist.objects.all().viewable_by_user(self.user)
            .filter(id=playlist.id).exists()
        )

        request = self.factory.get('/?playlist=' + playlist.id)
        force_authenticate(request, user=self.user)

        response = self.view(request)
        self.assertEqual(response.status_code, 400)  # bad request: playlist doesn't exist

    def test_token_auth_list(self):
        """A token-authenticated user should get expected media back."""
        token = Token.objects.create(user=self.user)
        token_get_request = self.factory.get('/', HTTP_AUTHORIZATION=f'Token {token.key}')
        response_data = self.view(token_get_request).data
        self.assertIn('results', response_data)

        # sanity check that the viewable lists differ
        self.assertNotEqual(self.viewable_by_user.count(), self.viewable_by_anon.count())

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.viewable_by_user.count())

        expected_ids = set(o.id for o in self.viewable_by_user)
        for item in response_data['results']:
            self.assertIn(item['id'], expected_ids)

    def test_search_by_title(self):
        """Items can be searched by title."""
        item = mpmodels.MediaItem.objects.first()
        item.title = 'some bananas'
        item.view_permission.is_public = True
        item.view_permission.save()
        item.save()
        self.assert_search_result(item, positive_query='Banana', negative_query='Pineapple')

    def test_search_by_description(self):
        """Items can be searched by description."""
        item = mpmodels.MediaItem.objects.first()
        item.description = 'some bananas'
        item.view_permission.is_public = True
        item.view_permission.save()
        item.save()
        self.assert_search_result(item, positive_query='Banana', negative_query='Pineapple')

    def test_search_by_tags(self):
        """Items can be searched by tags."""
        item = mpmodels.MediaItem.objects.first()
        item.tags = ['apples', 'oranges', 'top bananas']
        item.view_permission.is_public = True
        item.view_permission.save()
        item.save()
        self.assert_search_result(item, positive_query='Banana', negative_query='Pineapple')
        self.assert_search_result(item, positive_query='Banana', negative_query='Pineapple')

    def test_search_ordering(self):
        """Items are sorted by relevance from search endpoint."""
        items = mpmodels.MediaItem.objects.all()[:2]
        for item in items:
            item.view_permission.is_public = True
            item.view_permission.save()

        items[0].title = 'banana-y bananas are completely bananas'
        items[0].save()
        items[1].title = 'some bananas'
        items[1].save()

        # both items should appear in results
        for item in items:
            self.assert_search_result(item, positive_query='Banana')

        # item 0 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], items[0].id)

        # make item 1 more relevant
        items[1].description = (
            'Bananas with bananas can banana the banana. Bruce Banana is not the Hulk')
        items[1].save()

        # both items should still appear in results
        for item in items:
            self.assert_search_result(item, positive_query='Banana')

        # item 1 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], items[1].id)

    def assert_search_result(self, item, positive_query=None, negative_query=None):
        # Item should appear in relevant query
        if positive_query is not None:
            self.assertTrue(any(
                result_item['id'] == item.id
                for result_item in self.get_search_results(positive_query)
            ))

        # Item should not appear in irrelevant query
        if negative_query is not None:
            self.assertFalse(any(
                result_item['id'] == item.id
                for result_item in self.get_search_results(negative_query)
            ))

    def get_search_results(self, query):
        # this doesn't escape query which means tests should be kind in what they pass in here :)
        get_request = self.factory.get('/?search=' + query)
        response_data = self.view(get_request).data
        return response_data['results']


class MediaItemViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemView().as_view()
        self.dv_from_key_patcher = (
            mock.patch('mediaplatform_jwp.api.delivery.DeliveryVideo.from_key'))
        self.dv_from_key = self.dv_from_key_patcher.start()
        self.dv_from_key.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        self.addCleanup(self.dv_from_key_patcher.stop)

    def test_success(self):
        """Check that a media item is successfully returned"""
        item = self.non_deleted_media.get(id='populated')
        # Remove the associated SMS media items so that editing succeeds
        item.sms.delete()

        # test
        response = self.view(self.get_request, pk=item.id)
        self.assertEqual(response.status_code, 200)

        self.dv_from_key.assert_called_with(item.jwp.key)

        self.assertEqual(response.data['id'], item.id)
        self.assertEqual(response.data['title'], item.title)
        self.assertEqual(response.data['description'], item.description)
        self.assertEqual(dateparser.parse(response.data['publishedAt']), item.published_at)
        self.assertIsNotNone(response.data['posterImageUrl'])
        self.assertIsNotNone(response.data['duration'])

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
        # Remove the associated SMS media items so that editing succeeds
        item.sms.delete()

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
        # Remove the associated SMS media items so that editing succeeds
        item.sms.delete()
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
        # Remove the associated SMS media items so that editing succeeds
        item.sms.delete()
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
        # Remove the associated SMS media items so that editing succeeds
        item.sms.delete()
        item.channel.edit_permission.crsids.append(self.user.username)
        item.channel.edit_permission.save()
        new_channel = mpmodels.Channel.objects.create(
            title='new channel', billing_account=self.channels[0].billing_account)
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

        # Remove any associated SMS media items so item is editable
        if hasattr(item, 'sms'):
            item.sms.delete()

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

        # Remove any associated SMS media items so item is editable
        if hasattr(item, 'sms'):
            item.sms.delete()

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


@override_settings(
    JWPLATFORM_API_BASE_URL='http://jwp.invalid/',
    JWPLATFORM_EMBED_PLAYER_KEY='mock-key',
)
class MediaItemEmbedTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemEmbedView().as_view()
        self.item = self.non_deleted_media.get(id='populated')

    def test_basic_functionality(self):
        with mock.patch('time.time') as time:
            time.return_value = 123456
            expected_embed_url = api.player_embed_url(self.item.jwp.key, 'mock-key', format='js')
            response = self.view(self.get_request, pk=self.item.id)
        self.assertContains(response, '<script src="%s"></script>' % expected_embed_url, html=True)

    def test_visibility(self):
        """If an item has no visibility, the embed view should 404."""
        self.item.view_permission.reset()
        self.item.view_permission.save()
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()
        response = self.view(self.get_request, pk=self.item.id)
        self.assertEqual(response.status_code, 404)

    def test_no_jwp(self):
        """If an item has no JWP video, the embed view should 404."""
        self.item.jwp.delete()
        response = self.view(self.get_request, pk=self.item.id)
        self.assertEqual(response.status_code, 404)

    def test_custom_404(self):
        """For embed views, there is a custom 404 template."""
        non_existent_id = self.item.id + 'with-non-existent-suffix'
        login_url = '/mock/login/url'
        with self.settings(LOGIN_URL=login_url):
            response = self.client.get(
                reverse('api:media_embed', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'api/embed_404.html')
        self.assertIn(login_url, response.content.decode('utf8'))

    def test_custom_404_hides_login_if_not_signed_in(self):
        """For embed views, do not show the login link if the user is logged in."""
        non_existent_id = self.item.id + 'with-non-existent-suffix'
        login_url = '/mock/login/url'
        with self.settings(LOGIN_URL=login_url):
            self.client.force_login(self.user)
            response = self.client.get(
                reverse('api:media_embed', kwargs={'pk': non_existent_id}))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'api/embed_404.html')
        self.assertNotIn(login_url, response.content.decode('utf8'))


class MediaItemSourceViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemSourceView().as_view()
        self.item = self.non_deleted_media.get(id='populated')
        self.dv_from_key_patcher = (
            mock.patch('mediaplatform_jwp.api.delivery.DeliveryVideo.from_key'))
        self.dv_from_key = self.dv_from_key_patcher.start()
        self.dv_from_key.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        self.addCleanup(self.dv_from_key_patcher.stop)

        # Make sure item is downloadable
        self.item.downloadable = True
        self.item.save()

    def test_basic_functionality(self):
        source = DELIVERY_VIDEO_FIXTURE['sources'][0]
        response = self.get(
            mime_type=source['type'], width=source['width'], height=source['height'])
        self.assertRedirects(response, source['file'], fetch_redirect_response=False)

    def test_visibility(self):
        """If an item has no visibility, the source view should 404."""
        self.item.view_permission.reset()
        self.item.view_permission.save()
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()
        source = DELIVERY_VIDEO_FIXTURE['sources'][0]
        response = self.get(
            mime_type=source['type'], width=source['width'], height=source['height'])
        self.assertEqual(response.status_code, 404)

    def test_bad_width(self):
        """Non-integer width raises 400"""
        response = self.get(mime_type='video/mp4', width='1.23', height='1')
        self.assertEqual(response.status_code, 400)

    def test_bad_height(self):
        """Non-integer height raises 400"""
        response = self.get(mime_type='video/mp4', height='1.23', width='1')
        self.assertEqual(response.status_code, 400)

    def test_no_args(self):
        """Passing no arguments returns the "best" source."""
        sources = [
            {
                'type': 'video/mp4', 'width': 720, 'height': 406,
                'file': 'http://cdn.invalid/vid2.mp4',
            },
            {
                'type': 'video/mp4', 'width': 1920, 'height': 1080,
                'file': 'http://cdn.invalid/vid1.mp4',
            },
            {
                'type': 'audio/mp4', 'file': 'http://cdn.invalid/vid_audio.mp4',
            },
        ]
        self.dv_from_key.return_value = api.DeliveryVideo({
            **DELIVERY_VIDEO_FIXTURE, 'sources': sources
        })
        source = sources[1]
        response = self.get()
        self.assertRedirects(response, source['file'], fetch_redirect_response=False)

    def test_extension_ignored(self):
        """Test that the extension set on the media_source_with_ext endpoint is ignored"""
        source = DELIVERY_VIDEO_FIXTURE['sources'][0]
        response = self.client.get(
            reverse('api:media_source_with_ext', kwargs={
                'pk': self.item.id,
                'extension': 'mov'
            })
        )
        self.assertRedirects(response, source['file'], fetch_redirect_response=False)

    def test_audio_best_source(self):
        """Best source will include audio if that is all there is."""
        sources = [
            {
                'type': 'something/else', 'file': 'http://cdn.invalid/vid_odd.mp4',
            },
            {
                'type': 'audio/mp4', 'file': 'http://cdn.invalid/vid_audio.mp4',
            },
        ]
        self.dv_from_key.return_value = api.DeliveryVideo({
            **DELIVERY_VIDEO_FIXTURE, 'sources': sources
        })
        source = sources[1]
        response = self.get()
        self.assertRedirects(response, source['file'], fetch_redirect_response=False)

    def get(self, mime_type=None, width=None, height=None, item=None):
        item = item if item is not None else self.item
        query = QueryDict(mutable=True)
        if mime_type is not None:
            query['mimeType'] = mime_type
        if width is not None:
            query['width'] = f'{width}'
        if height is not None:
            query['height'] = f'{height}'
        return self.client.get(
            reverse('api:media_source', kwargs={'pk': item.id}) + '?' + query.urlencode()
        )


class MediaItemPosterViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.MediaItemPosterView().as_view()
        self.item = self.non_deleted_media.get(id='populated')
        self.video = api.DeliveryVideo({'key': self.item.jwp.key})

    def test_basic_functionality(self):
        response = self.get(width=320)
        self.assertRedirects(
            response, self.video.get_poster_url(width=320), fetch_redirect_response=False)

    def test_404_for_hidden_item(self):
        """If an item is not viewable (or doesn't exist) a 404 is returned."""
        # Succeeds initially
        response = self.get(width=320)
        self.assertRedirects(
            response, self.video.get_poster_url(width=320), fetch_redirect_response=False)

        # Hide item
        self.item.view_permission.reset()
        self.item.view_permission.save()

        # Now 404s
        response = self.get(width=320)
        self.assertEqual(response.status_code, 404)

    def test_valid_widths(self):
        """For valid widths, a redirect response should be generated."""
        for width in views.POSTER_IMAGE_VALID_WIDTHS:
            response = self.get(width=width)
            self.assertRedirects(
                response, self.video.get_poster_url(width=width), fetch_redirect_response=False)

    def test_invalid_widths(self):
        """For invalid widths, a 404 should be generated."""
        invalid_widths = [0, 100, 1000000]
        for width in invalid_widths:
            assert width not in views.POSTER_IMAGE_VALID_WIDTHS
            response = self.get(width=width)
            self.assertEqual(response.status_code, 404)

    def test_invalid_extensions(self):
        """For valid widths, invalid extensions should fail."""
        invalid_extensions = ['foo']
        for extension in invalid_extensions:
            for width in views.POSTER_IMAGE_VALID_WIDTHS:
                response = self.get(width=width, extension=extension)
                self.assertEqual(response.status_code, 404)

    def get(self, width, extension='jpg', item=None):
        item = item if item is not None else self.item
        return self.client.get(
            reverse('api:media_poster', kwargs={
                'pk': item.id, 'width': width, 'extension': extension,
            })
        )


class UploadEndpointTestCase(ViewTestCase):
    fixtures = ['api/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        super().setUp()
        self.view = views.MediaItemUploadView().as_view()
        self.item = mpmodels.MediaItem.objects.get(id='populated')

        # Remove the associated SMS media items
        self.item.sms.delete()

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

        with mock.patch('mediaplatform_jwp.api.management.create_upload_endpoint'
                        ) as mock_create:
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
        item.jwp.resource.data['size'] = 12345
        item.jwp.resource.save()
        media_id = item.sms.id
        add_stat(day=datetime.date(2018, 5, 17), num_hits=3, media_id=media_id)
        add_stat(day=datetime.date(2018, 3, 22), num_hits=4, media_id=media_id)

        # test
        response = views.MediaItemAnalyticsView().as_view()(self.get_request, pk=item.id)

        self.assertEqual(response.status_code, 200)

        views_per_day = response.data['views_per_day']

        self.assertEqual(views_per_day[0]['date'], '2018-05-17')
        self.assertEqual(views_per_day[0]['views'], 3)
        self.assertEqual(views_per_day[1]['date'], '2018-03-22')
        self.assertEqual(views_per_day[1]['views'], 4)

        self.assertEqual(response.data['size'], 12345)

    def test_no_legacy_sms(self):
        """
        Check that no analytics are returned if a media item doesn't have a legacysms.MediaItem
        """
        item = self.non_deleted_media.get(id='a')
        item.jwp.resource.data['size'] = 54321
        item.jwp.resource.save()

        # test
        response = views.MediaItemAnalyticsView().as_view()(self.get_request, pk=item.id)

        self.assertEqual(response.status_code, 200)

        views_per_day = response.data['views_per_day']

        self.assertEqual(len(views_per_day), 0)

        # also check that size is still populated
        self.assertEqual(response.data['size'], 54321)


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

    def test_search_by_title(self):
        """Channels can be searched by title."""
        channel = mpmodels.Channel.objects.first()
        channel.title = 'some bananas'
        channel.save()
        self.assert_search_result(channel, positive_query='Banana', negative_query='Pineapple')

    def test_search_by_description(self):
        """Channels can be searched by description."""
        channel = mpmodels.Channel.objects.first()
        channel.description = 'some bananas'
        channel.save()
        self.assert_search_result(channel, positive_query='Banana', negative_query='Pineapple')

    def test_search_ordering(self):
        """Channels are sorted by relevance from search endpoint."""
        channels = mpmodels.Channel.objects.all()[:2]
        channel1 = channels[0]
        channel2 = channels[1]

        channel1.title = 'banana-y bananas are completely bananas'
        channel1.save()
        self.assert_search_result(channel1, positive_query='Banana')

        channel2.title = 'some bananas'
        channel2.save()
        self.assert_search_result(channel2, positive_query='Banana')

        # channel1 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], channel1.id)

        # make channel2 more relevant
        channel2.description = (
            'Bananas with bananas can banana the banana. Bruce Banana is not the Hulk')
        channel2.save()
        self.assert_search_result(channel2, positive_query='Banana')

        # channel2 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], channel2.id)

    def test_create_with_billing_account_without_permission(self):
        """Creation of a channel fails if the user does not have rights on the billing account."""
        self.assertNotIn(
            self.user.username,
            self.unused_billing_account.channel_create_permission.crsids)
        request = self.factory.post('/', {
            'title': 'foo', 'billingAccountId': self.unused_billing_account.id
        })
        force_authenticate(request, user=self.user)
        response = self.view(request)
        # The missing field has an error message in the response
        self.assertIn('billingAccountId', response.data)
        self.assertEqual(response.status_code, 400)

    def test_create_without_billing_account_fails(self):
        """Creation of a channel requires billing account."""
        request = self.factory.post('/', {'title': 'foo'})
        force_authenticate(request, user=self.user)
        response = self.view(request)
        # The missing field has an error message in the response
        self.assertIn('billingAccountId', response.data)
        self.assertEqual(response.status_code, 400)

    def test_create_with_billing_account_with_permission(self):
        """Creation of a channel succeeds if the user *does* have rights on the billing account."""
        self.unused_billing_account.channel_create_permission.crsids.append(self.user.username)
        self.unused_billing_account.channel_create_permission.save()
        request = self.factory.post('/', {
            'title': 'foo', 'billingAccountId': self.unused_billing_account.id
        })
        force_authenticate(request, user=self.user)
        response = self.view(request)
        print(response.data)
        self.assertEqual(response.status_code, 201)

        # The created channel has the billing account set and edit permissions for the user.
        self.assertIn('id', response.data)
        channel = mpmodels.Channel.objects.get(id=response.data['id'])
        self.assertEqual(channel.billing_account.id, self.unused_billing_account.id)
        self.assertIn(self.user.username, channel.edit_permission.crsids)

    def assert_search_result(self, channel, positive_query=None, negative_query=None):
        # Channels should appear in relevant query
        if positive_query is not None:
            self.assertTrue(any(
                result_item['id'] == channel.id
                for result_item in self.get_search_results(positive_query)
            ))

        # Channels should not appear in irrelevant query
        if negative_query is not None:
            self.assertFalse(any(
                result_item['id'] == channel.id
                for result_item in self.get_search_results(negative_query)
            ))

    def get_search_results(self, query):
        # this doesn't escape query which means tests should be kind in what they pass in here :)
        get_request = self.factory.get('/?search=' + query)
        response_data = self.view(get_request).data
        return response_data['results']


class ChannelViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.ChannelView().as_view()
        # A suitable test channel
        self.channel = self.channels.get(id='channel1')

        # There needs to be at least one billing account that the user can create channels on. Give
        # them rights on all of them.
        for account in mpmodels.BillingAccount.objects.all():
            account.channel_create_permission.crsids.append(self.user.username)
            account.channel_create_permission.save()

    def test_success(self):
        """Check that a channel is successfully returned"""
        response = self.view(self.get_request, pk=self.channel.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.channel.id)
        self.assertEqual(response.data['title'], self.channel.title)

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

    def test_created_at_immutable(self):
        self.assert_field_immutable('createdAt', '2018-08-06T15:29:45.003231Z', 'created_at')

    def test_billing_account_immutable_with_permission(self):
        """Attempting to change the billing account to one user *has* channel create permission on
        fails."""
        accounts = mpmodels.BillingAccount.objects.all()
        self.assertTrue(accounts.exists())

        # Try setting account id to all accounts user has access to.
        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()
        for account in accounts:
            self.assertIn(self.user.username, account.channel_create_permission.crsids)
            request = self.factory.patch(
                '/', {'billingAccountId': account.id}, format='json')
            force_authenticate(request, user=self.user)
            response = self.view(request, pk=self.channel.id)
            self.assertEqual(response.status_code, 400)

    def test_billing_account_immutable_without_permission(self):
        """Attempting to change the billing account to one user *does not have* channel create
        permission on fails."""
        accounts = mpmodels.BillingAccount.objects.all()
        self.assertTrue(accounts.exists())

        for account in accounts:
            account.channel_create_permission.reset()
            account.channel_create_permission.save()

        # Try setting account id to all accounts user has access to.
        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()
        for account in mpmodels.BillingAccount.objects.all():
            self.assertNotIn(self.user.username, account.channel_create_permission.crsids)
            request = self.factory.patch(
                '/', {'billingAccountId': account.id}, format='json')
            force_authenticate(request, user=self.user)
            response = self.view(request, pk=self.channel.id)
            self.assertEqual(response.status_code, 400)

    def test_media_item_count(self):
        """Check that a count of media items are returned for the channel"""
        # Tweak items to make sure count of items viewable to user and public are different
        items = mpmodels.MediaItem.objects.all()[:2]
        for i in items:
            i.channel = self.channel
            i.save()

        items[0].view_permission.reset()
        items[0].view_permission.is_public = True
        items[0].view_permission.save()
        items[1].view_permission.reset()
        items[1].view_permission.is_signed_in = True
        items[1].view_permission.save()

        public_count = self.channel.items.all().viewable_by_user(None).count()
        signed_in_count = self.channel.items.all().viewable_by_user(self.user).count()
        self.assertGreater(signed_in_count, public_count)

        response = self.view(self.get_request, pk=self.channel.id)
        self.assertEqual(response.data['mediaCount'], public_count)

        force_authenticate(self.get_request, user=self.user)
        response = self.view(self.get_request, pk=self.channel.id)
        self.assertEqual(response.data['mediaCount'], signed_in_count)

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


class PlaylistListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.PlaylistListView().as_view()
        self.channel = mpmodels.Channel.objects.get(id='channel1')
        self.channel.edit_permission.reset()
        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()

    def test_basic_list(self):
        """An anonymous user should get expected playlists back."""
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.playlists_visibile_by_anon.count())

        expected_ids = set(o.id for o in self.playlists_visibile_by_anon)
        for item in response_data['results']:
            self.assertIn(item['id'], expected_ids)

    def test_auth_list(self):
        """An authenticated user should get expected playlists back."""
        force_authenticate(self.get_request, user=self.user)
        response_data = self.view(self.get_request).data
        self.assertIn('results', response_data)

        # sanity check that the viewable lists differ
        self.assertNotEqual(self.playlists_visibile_by_user.count(),
                            self.playlists_visibile_by_anon.count())

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(len(response_data['results']), self.playlists_visibile_by_user.count())

        expected_ids = set(o.id for o in self.playlists_visibile_by_user)
        for item in response_data['results']:
            self.assertIn(item['id'], expected_ids)

    def test_create(self):
        """Basic creation of a playlist succeeds."""
        request = self.factory.post('/', {'title': 'foo', 'channelId': self.channel.id})
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)
        new_playlist = mpmodels.Playlist.objects.get(id=response.data['id'])
        self.assertEqual(new_playlist.channel.id, self.channel.id)
        self.assertEqual(new_playlist.title, 'foo')

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

    def test_search_by_title(self):
        """Playlist can be searched by title."""
        playlist = mpmodels.Playlist.objects.first()
        playlist.title = 'some bananas'
        playlist.view_permission.is_public = True
        playlist.view_permission.save()
        playlist.save()
        self.assert_search_result(playlist, positive_query='Banana', negative_query='Pineapple')

    def test_search_by_description(self):
        """Playlist can be searched by description."""
        playlist = mpmodels.Playlist.objects.first()
        playlist.description = 'some bananas'
        playlist.view_permission.is_public = True
        playlist.view_permission.save()
        playlist.save()
        self.assert_search_result(playlist, positive_query='Banana', negative_query='Pineapple')

    def test_search_ordering(self):
        """Playlists are sorted by relevance from search endpoint."""
        playlists = mpmodels.Playlist.objects.all()[:2]
        for playlist in playlists:
            playlist.view_permission.is_public = True
            playlist.view_permission.save()

        playlists[0].title = 'banana-y bananas are completely bananas'
        playlists[0].save()
        playlists[1].title = 'some bananas'
        playlists[1].save()

        # both items should appear in results
        for playlist in playlists:
            self.assert_search_result(playlist, positive_query='Banana')

        # item 0 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], playlists[0].id)

        # make item 1 more relevant
        playlists[1].description = (
            'Bananas with bananas can banana the banana. Bruce Banana is not the Hulk')
        playlists[1].save()

        # both items should still appear in results
        for playlist in playlists:
            self.assert_search_result(playlist, positive_query='Banana')

        # item 1 should be first
        results = self.get_search_results('Banana')
        self.assertEqual(results[0]['id'], playlists[1].id)

    def assert_search_result(self, item, positive_query=None, negative_query=None):
        # Playlist should appear in relevant query
        if positive_query is not None:
            self.assertTrue(any(
                result_item['id'] == item.id
                for result_item in self.get_search_results(positive_query)
            ))

        # Playlist should not appear in irrelevant query
        if negative_query is not None:
            self.assertFalse(any(
                result_item['id'] == item.id
                for result_item in self.get_search_results(negative_query)
            ))

    def get_search_results(self, query):
        # this doesn't escape query which means tests should be kind in what they pass in here :)
        get_request = self.factory.get('/?search=' + query)
        response_data = self.view(get_request).data
        return response_data['results']


class PlaylistViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.PlaylistView().as_view()

    def test_success(self):
        """Check that a playlist is successfully returned"""
        playlist = self.playlists.get(id='public')
        response = self.view(self.get_request, pk=playlist.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], playlist.id)
        self.assertEqual(response.data['title'], playlist.title)
        self.assertEqual(response.data['description'], playlist.description)
        self.assertEqual(response.data['mediaIds'], playlist.media_items)

    def test_no_permissions(self):
        """Check that a playlist is not returned if user does not have permission to view"""
        response = self.view(self.get_request, pk='crsidsperm')
        self.assertEqual(response.status_code, 404)

    def test_not_found(self):
        """Check that a 404 is returned if no playlist is found"""
        response = self.view(self.get_request, pk='this-playlist-id-does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_deleted_not_found(self):
        """Check that a 404 is returned if a deleted playlist is asked for."""
        deleted_playlist = (
            self.playlists_including_deleted.filter(deleted_at__isnull=False).first())
        self.assertIsNotNone(deleted_playlist)
        response = self.view(self.get_request, pk=deleted_playlist.id)
        self.assertEqual(response.status_code, 404)

    def test_delete_success(self):
        """Check that a playlist is successfully deleted"""

        # give user edit privilege
        self.channel = mpmodels.Channel.objects.get(id='channel1')
        self.channel.edit_permission.reset()
        self.channel.edit_permission.crsids.append(self.user.username)
        self.channel.edit_permission.save()

        # test
        self.client.force_login(self.user)
        response = self.client.delete(reverse('api:playlist', kwargs={'pk': 'public'}))

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(self.playlists.filter(id='public').first())

    def test_delete_no_perm(self):
        """Check that a user doesn't have permission to delete playlist"""

        # test
        self.client.force_login(self.user)
        response = self.client.delete(reverse('api:playlist', kwargs={'pk': 'public'}))

        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(self.playlists.filter(id='public').first())

    def test_id_immutable(self):
        self.assert_field_immutable('id')

    def test_title_mutable(self):
        self.assert_field_mutable('title')

    def test_description_mutable(self):
        self.assert_field_mutable('description')

    def test_media_items_mutable(self):
        self.assert_field_mutable('mediaIds', ['public'], 'media_items')

    def test_channel_id_immutable(self):
        new_channel = mpmodels.Channel.objects.get(id='channel2')
        new_channel.edit_permission.crsids.append(self.user.username)
        new_channel.edit_permission.save()
        self.assert_field_immutable('channel_id', new_channel.id)

    def test_channel_immutable(self):
        new_channel = mpmodels.Channel.objects.get(id='channel2')
        new_channel.edit_permission.crsids.append(self.user.username)
        new_channel.edit_permission.save()
        self.assert_field_immutable('channel', new_channel.id)

    def test_created_at_immutable(self):
        self.assert_field_immutable('createdAt', '2018-08-06T15:29:45.003231Z', 'created_at')

    def test_media_appears_in_response(self):
        """
        Check that a playlist detail view includes all of the media.
        """
        playlist = self.playlists.get(id='public')
        self.assertGreater(len(playlist.ordered_media_item_queryset), 0)
        expected_ids = [m.id for m in playlist.ordered_media_item_queryset]

        # Make sure the anonymous user can see all media items
        for item in playlist.ordered_media_item_queryset:
            item.view_permission.is_public = True
            item.view_permission.save()

        response = self.view(self.get_request, pk=playlist.id)
        self.assertEqual(response.status_code, 200)

        # Check that all media items appear in the detail view in the right order
        returned_media_ids = [m['id'] for m in response.data['media']]
        self.assertEqual(expected_ids, returned_media_ids)

    def test_media_respects_view_permission(self):
        """
        Check that a playlist detail view does not include media the user has no view permission
        on. (Even if the returned list of ids contains it.)
        """
        playlist = self.playlists.get(id='public')
        self.assertGreater(len(playlist.ordered_media_item_queryset), 1)

        # Make sure the anonymous user can see all media items
        for item in playlist.ordered_media_item_queryset:
            item.view_permission.is_public = True
            item.view_permission.save()

        # Except the second one
        invisible_item = playlist.ordered_media_item_queryset[1]
        invisible_item.view_permission.reset()
        invisible_item.view_permission.save()

        expected_ids = [
            m.id for m in playlist.ordered_media_item_queryset
            if m.id != invisible_item.id
        ]

        response = self.view(self.get_request, pk=playlist.id)
        self.assertEqual(response.status_code, 200)

        # Check that all expected media items appear in the detail view in the right order
        returned_media_ids = [m['id'] for m in response.data['media']]
        self.assertEqual(expected_ids, returned_media_ids)

    def assert_field_mutable(
            self, field_name, new_value='testvalue', model_field_name=None, expected_value=None):
        expected_value = expected_value or new_value
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        playlist = self.playlists.get(id='emptyperm')

        playlist.channel.edit_permission.crsids.append(self.user.username)
        playlist.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=playlist.id)
        self.assertEqual(response.status_code, 403)

        force_authenticate(request, user=self.user)
        response = self.view(request, pk=playlist.id)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            getattr(self.playlists.get(id=playlist.id), model_field_name), expected_value)

    def assert_field_immutable(self, field_name, new_value='test value', model_field_name=None):
        model_field_name = model_field_name or field_name
        request = self.factory.patch('/', {field_name: new_value}, format='json')

        playlist = self.playlists.get(id='emptyperm')

        playlist.channel.edit_permission.crsids.append(self.user.username)
        playlist.channel.edit_permission.save()

        # Unauthorised request should fail
        response = self.view(request, pk=playlist.id)
        self.assertEqual(response.status_code, 403)

        # Authorised request should have no effect
        original_value = getattr(playlist, model_field_name)
        self.assertNotEqual(original_value, new_value)
        force_authenticate(request, user=self.user)
        response = self.view(request, pk=playlist.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            getattr(self.playlists.get(id=playlist.id), model_field_name), original_value)


class BillingAccountListViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.BillingAccountListView().as_view()

    def test_basic_list(self):
        """A user should get expected accounts back."""
        request = self.factory.get('/')
        force_authenticate(request, user=self.user)
        response_data = self.view(request).data
        self.assertIn('results', response_data)

        self.assertNotEqual(len(response_data['results']), 0)
        self.assertEqual(
            len(response_data['results']), mpmodels.BillingAccount.objects.count())

    def test_can_create_channels_filter(self):
        """One should be able to filter be billing accounts where the user has permission to
        create channels."""
        account = mpmodels.BillingAccount.objects.get(id='bacct1')
        account.channel_create_permission.crsids.append(self.user.username)
        account.channel_create_permission.save()

        # Reset all other billing account permissions
        for a in mpmodels.BillingAccount.objects.all():
            if a.id == account.id:
                continue
            a.channel_create_permission.reset()
            a.channel_create_permission.save()

        can_create_accounts = (
            mpmodels.BillingAccount.objects.all()
            .annotate_can_create_channels(self.user)
            .filter(can_create_channels=True)
        )

        # Note: cannot use .count() here because of a Django ORM bug giving rise the the dreaded
        # "unhashable type: list" exception.
        self.assertEqual(len(list(can_create_accounts)), 1)
        self.assertIn(account.id, [a.id for a in can_create_accounts])

        request = self.factory.get('/?canCreateChannels=true')
        force_authenticate(request, user=self.user)
        response_data = self.view(request).data
        self.assertIn('results', response_data)
        results = response_data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], account.id)

        request = self.factory.get('/?canCreateChannels=false')
        force_authenticate(request, user=self.user)
        response_data = self.view(request).data
        self.assertIn('results', response_data)
        results = response_data['results']
        self.assertGreater(len(results), 1)
        self.assertNotIn(account.id, [a['id'] for a in results])


class BillingAccountViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.view = views.BillingAccountView().as_view()
        self.channel = mpmodels.Channel.objects.get(id='channel1')
        self.billing_account = self.channel.billing_account

    def test_success(self):
        """A billing account item is successfully returned bu the api"""
        response = self.view(self.get_request, pk=self.billing_account.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.billing_account.id)
        self.assertEqual(response.data['description'], self.billing_account.description)

    def test_channel_list(self):
        """A list of channels for the billing account is returned."""
        channels = self.billing_account.channels
        self.assertGreater(channels.count(), 0)
        response = self.view(self.get_request, pk=self.billing_account.id)
        self.assertEqual(response.status_code, 200)

        expected_ids = {c.id for c in channels.all()}
        self.assertEqual({c['id'] for c in response.data['channels']}, expected_ids)

    def test_not_found(self):
        """A 404 is returned if no billing account is found"""
        response = self.view(self.get_request, pk='this-id-does-not-exist')
        self.assertEqual(response.status_code, 404)

    # TODO: test mutable/immutable fields when billing account becomes mutable.


DELIVERY_VIDEO_FIXTURE = {
    'key': 'mock1',
    'title': 'Mock 1',
    'description': 'Description for mock 1',
    'date': 1234567,
    'duration': 54,
    'sms_acl': 'acl:WORLD:',
    'sms_media_id': 'media:1234:',
    'sources': [
        {
            'type': 'video/mp4', 'width': 1920, 'height': 1080,
            'file': 'http://cdn.invalid/vid1.mp4',
        },
        {
            'type': 'video/mp4', 'width': 720, 'height': 406,
            'file': 'http://cdn.invalid/vid2.mp4',
        },
    ],
}
