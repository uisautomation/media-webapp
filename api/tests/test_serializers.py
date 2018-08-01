from unittest import mock

from django.test import TestCase

from .. import serializers


class MediaItemSerializerTestCase(TestCase):
    def test_create_with_no_user(self):
        with mock.patch('mediaplatform.models.MediaItem.objects.create') as f:
            serializers.MediaSerializer().create(validated_data={})
        f.assert_called()

        request = mock.MagicMock()
        request.user.is_anonymous = False
        request.user.username = 'testuser'
        with mock.patch('mediaplatform.models.MediaItem.objects.create_for_user') as f:
            serializers.MediaSerializer(context={'request': request}).create(validated_data={})
        f.assert_called()
