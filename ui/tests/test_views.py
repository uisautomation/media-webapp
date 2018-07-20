"""
Tests for views.

"""
import json
from unittest import mock

from django.urls import reverse

import smsjwplatform.jwplatform as api
from api.tests.test_views import ViewTestCase, DELIVERY_VIDEO_FIXTURE


class ViewsTestCase(ViewTestCase):

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_success(self, mock_from_id):
        """checks that a media item is rendered successfully"""
        mock_from_id.return_value = api.DeliveryVideo(DELIVERY_VIDEO_FIXTURE)
        item = self.non_deleted_media.get(id='populated')

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': item.pk}))

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'ui/media.html')
        self.assertEqual(r.context['title'], item.title)
        media_item_json = json.loads(r.context['media_item_json'])
        self.assertEqual(
            media_item_json['poster_image_url'],
            'https://cdn.jwplayer.com/thumbs/{}-720.jpg'.format(item.jwp.key)
        )

    @mock.patch('smsjwplatform.jwplatform.DeliveryVideo.from_key')
    def test_video_not_found(self, mock_from_id):
        """checks that a video not found results in a 404"""
        mock_from_id.side_effect = api.VideoNotFoundError

        # test
        r = self.client.get(reverse('ui:media_item', kwargs={'pk': 'this-does-not-exist'}))

        self.assertEqual(r.status_code, 404)

    # TODO: add ACL checks here
