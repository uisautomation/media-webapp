"""
Tests for views.

"""
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse

from mediaplatform import models as mpmodels
import mediaplatform_jwp.api.delivery as api
from api.tests.test_views import ViewTestCase as _ViewTestCase, DELIVERY_VIDEO_FIXTURE


class ViewTestCase(_ViewTestCase):
    def setUp(self):
        super().setUp()
        dv_patch = mock.patch('mediaplatform_jwp.api.delivery.DeliveryVideo.from_key')
        self.mock_from_id = dv_patch.start()
        self.mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        self.addCleanup(dv_patch.stop)

        get_person_patch = mock.patch('automationlookup.get_person')
        self.get_person = get_person_patch.start()
        self.get_person.return_value = {}
        self.addCleanup(get_person_patch.stop)


class MediaViewTestCase(ViewTestCase):
    def test_success(self):
        """checks that a media item is rendered successfully"""
        item = self.non_deleted_media.get(id='populated')

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        media_item_json = r.context['json_ld']
        self.assertEqual(media_item_json['name'], item.title)
        self.assertIn(
            'https://cdn.jwplayer.com/thumbs/{}-1280.jpg'.format(item.jwp.key),
            media_item_json['thumbnailUrl'],
        )

    def test_video_not_found(self):
        """checks that a video not found results in a 404"""
        self.mock_from_id.side_effect = api.VideoNotFoundError

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': 'this-does-not-exist'}))

        self.assertEqual(r.status_code, 404)

    def test_json_ld_embedded(self):
        """check that a JSON-LD script tag is present in the output"""
        item = self.non_deleted_media.get(id='populated')
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        content = r.content.decode('utf8')
        self.assertIn('<script type="application/ld+json">', content)

    def test_no_html_in_page(self):
        """checks that HTML in descriptions, etc is escaped."""
        self.mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        item = self.non_deleted_media.get(id='populated')

        item.title = '<some-tag>'
        item.save()

        r = self.client.get(reverse('ui:media_item', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        content = r.content.decode('utf8')
        self.assertNotIn('<some-tag>', content)

    def test_profile(self):
        """check that the user's profile is embedded in the page."""
        item = self.non_deleted_media.get(id='populated')
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        content = r.content.decode('utf8')
        self.assertIn('<script type="application/profile+json">', content)


class UploadViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create(username='spqr1')

    def test_requires_login(self):
        r = self.client.get(reverse('ui:media_item_new'))
        self.assertNotEqual(r.status_code, 200)
        self.client.force_login(self.user)
        r = self.client.get(reverse('ui:media_item_new'))
        self.assertEqual(r.status_code, 200)


class IndexViewTestCase(ViewTestCase):
    def test_gtag(self):
        """Checks that the gtag is rendered into the page"""
        gtag_id = 'fjwbgrbgwywevywevwebjknwekjberhbgj'

        # Tag doesn't appear by default if setting is absent
        with override_settings(GTAG_ID=gtag_id):
            del settings.GTAG_ID
            r = self.client.get(reverse('ui:home'))
            self.assertNotIn(gtag_id, r.content.decode('utf8'))

        # Tag doesn't appear is setting is blank or None
        with self.settings(GTAG_ID=''):
            r = self.client.get(reverse('ui:home'))
        self.assertNotIn(gtag_id, r.content.decode('utf8'))

        with self.settings(GTAG_ID=None):
            r = self.client.get(reverse('ui:home'))
        self.assertNotIn(gtag_id, r.content.decode('utf8'))

        # Tag appears if setting is set
        with self.settings(GTAG_ID=gtag_id):
            r = self.client.get(reverse('ui:home'))
        self.assertIn(gtag_id, r.content.decode('utf8'))


class ChannelViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.channel = mpmodels.Channel.objects.get(id='channel1')

    def test_success(self):
        """A channel page renders."""
        r = self.client.get(reverse('ui:channel', kwargs={'pk': self.channel.id}))
        self.assertEqual(r.status_code, 200)


class PlaylistViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.playlist = mpmodels.Playlist.objects.get(id='public')

    def test_success(self):
        """A playlist page renders."""
        r = self.client.get(reverse('ui:playlist', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)


class MediaRSSViewTestCase(ViewTestCase):
    def setUp(self):
        self.lookup_groupids_and_instids_for_user_patcher = mock.patch(
                'mediaplatform.models._lookup_groupids_and_instids_for_user')
        self.lookup_groupids_and_instids_for_user = (
            self.lookup_groupids_and_instids_for_user_patcher.start())
        self.lookup_groupids_and_instids_for_user.return_value = ([], [])
        self.addCleanup(self.lookup_groupids_and_instids_for_user_patcher.stop)

        # Make sure there is a public downloadable item to render
        self.item = mpmodels.MediaItem.objects.get(id='populated')
        self.item.view_permission.reset()
        self.item.view_permission.is_public = True
        self.item.view_permission.save()
        self.item.downloadable = True
        self.item.save()

        self.new_user = get_user_model().objects.create(username='newuser')

    def test_success(self):
        """A downloadable viewable media item renders a RSS feed."""
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.item.title, r.content.decode('utf-8'))

    def test_non_downloadable(self):
        """A non-downloadable item results in a 404."""
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)
        self.item.downloadable = False
        self.item.save()
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)

    def test_super_downloader(self):
        """A user with mediaplatform.download_mediaitem permission can always download."""
        self.item.downloadable = False
        self.item.save()
        self.client.force_login(self.new_user)

        # initially cannot see the item
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)

        # add the permission to the user
        view_permission = Permission.objects.get(
            codename='download_mediaitem', content_type__app_label='mediaplatform')
        self.new_user.user_permissions.add(view_permission)
        self.new_user.save()

        # can now see the item
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)

    def test_non_visible(self):
        """A non-visible item results in a 404."""
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)
        self.item.view_permission.reset()
        self.item.view_permission.save()
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)

    def test_super_viewer(self):
        """A user with mediaplatform.view_mediaitem permission can always view if download set."""
        self.item.view_permission.reset()
        self.item.view_permission.save()
        self.client.force_login(self.new_user)

        # initially cannot see the item
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)

        # add the permission to the user
        view_permission = Permission.objects.get(
            codename='view_mediaitem', content_type__app_label='mediaplatform')
        self.new_user.user_permissions.add(view_permission)
        self.new_user.save()

        # can now see the item
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)

        # remove downloadable
        self.item.downloadable = False
        self.item.save()

        # cannot see the item any more
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)

    def test_non_sms(self):
        """A media item not visible unless it came from the SMS."""
        # initially OK
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 200)

        # delete related SMS objed
        self.item.sms.delete()

        # should not be visible
        r = self.client.get(reverse('ui:media_item_rss', kwargs={'pk': self.item.pk}))
        self.assertEqual(r.status_code, 404)


class PlaylistRSSViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        # Create a playlist
        channel = self.channels.first()
        self.playlist = mpmodels.Playlist.objects.create(channel=channel, title='Testing playlist')

        # Add first couple of media items to playlist and make sure that they are publicly viewable
        # and downloadable.
        self.assertGreater(mpmodels.MediaItem.objects.count(), 2)
        for idx, item in enumerate(mpmodels.MediaItem.objects.all()[:2]):
            item.title = f'Title for test item {idx}'
            item.description = f'Description for test item {idx}'
            item.downloadable = True
            item.view_permission.reset()
            item.view_permission.is_public = True
            item.view_permission.save()
            item.save()
            self.playlist.media_items.append(item.id)
        self.playlist.save()

    def test_basic_functionality(self):
        r = self.client.get(reverse('ui:playlist_rss', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf8')

        for item in self.playlist.ordered_media_item_queryset:
            self.assertIn(item.title, content)
            self.assertIn(item.description, content)

    def test_respects_visibility(self):
        item = self.playlist.ordered_media_item_queryset.first()
        item.view_permission.reset()
        item.view_permission.crsids.append(self.user.username)
        item.view_permission.save()

        # Private item does not appear for anonymous user
        r = self.client.get(reverse('ui:playlist_rss', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf8')
        self.assertNotIn(item.title, content)

        # Private item *does* appear for the correct user
        self.client.force_login(self.user)
        r = self.client.get(reverse('ui:playlist_rss', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf8')
        self.assertIn(item.title, content)

    def test_respects_downloadable(self):
        item = self.playlist.ordered_media_item_queryset.first()

        # Item does usually appear
        r = self.client.get(reverse('ui:playlist_rss', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf8')
        self.assertIn(item.title, content)

        # Clear downloadable flag
        item.downloadable = False
        item.save()

        # Item does not appear
        r = self.client.get(reverse('ui:playlist_rss', kwargs={'pk': self.playlist.id}))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf8')
        self.assertNotIn(item.title, content)
