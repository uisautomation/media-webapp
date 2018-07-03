"""
Tests for views.

"""
import json
from unittest import mock

from django.test import TestCase

from django.urls import reverse

import smsjwplatform.jwplatform as api
from api.tests.test_views import DELIVERY_VIDEO_FIXTURE


class ViewsTestCase(TestCase):

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_success(self, mock_from_id):
        """checks that a media item is rendered successfully"""
        mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'media_key': 'XYZ123'}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        self.assertEqual(r.context['title'], 'Mock 1')
        media_item_json = json.loads(r.context['media_item_json'])
        self.assertEqual(
            media_item_json['poster_image_url'], 'https://cdn.jwplayer.com/thumbs/mock1-720.jpg'
        )

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_video_not_found(self, mock_from_id):
        """checks that a video not found results in a 404"""
        mock_from_id.side_effect = api.VideoNotFoundError

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'media_key': 'XYZ123'}))

        self.assertEqual(r.status_code, 404)

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_no_access_to_video(self, mock_from_id):
        """Check that a 403 is returned the caller isn't the ACL"""
        mock_from_id.return_value = api.DeliveryVideo(
            {**DELIVERY_VIDEO_FIXTURE, 'sms_acl': 'acl:CAM:'}
        )

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'media_key': 'XYZ123'}))

        self.assertEqual(r.status_code, 403)
