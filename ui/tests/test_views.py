"""
Tests for views.

"""
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
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
