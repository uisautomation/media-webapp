"""
Tests for views.

"""
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.urls import reverse

import mediaplatform_jwp.jwplatformapi.deliveryapi as api
from api.tests import create_stats_table, delete_stats_table
from api.tests.test_views import ViewTestCase as _ViewTestCase, DELIVERY_VIDEO_FIXTURE


class ViewTestCase(_ViewTestCase):
    def setUp(self):
        super().setUp()
        dv_patch = mock.patch('mediaplatform_jwp.jwplatformapi.deliveryapi.DeliveryVideo.from_key')
        self.mock_from_id = dv_patch.start()
        self.mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        self.addCleanup(dv_patch.stop)

        get_profile_patch = mock.patch('api.views.get_profile')
        self.get_profile = get_profile_patch.start()
        self.get_profile.return_value = {'user': AnonymousUser()}
        self.addCleanup(get_profile_patch.stop)


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


class MediaItemAnalyticsViewTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        create_stats_table()
        self.addCleanup(delete_stats_table)

    def test_success(self):
        """checks that a media item's analytics are rendered successfully"""

        item = self.non_deleted_media.get(id='populated')

        # test
        r = self.client.get(reverse('ui:media_item_analytics', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/analytics.html')
        self.assertEqual(len(r.context['analytics']['results']), 0)


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
