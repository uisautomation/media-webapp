from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

import mediaplatform.models as mpmodels

from .. import serializers


class MediaItemSerializerTestCase(TestCase):
    def test_create(self):
        with mock.patch('mediaplatform.models.MediaItem.objects.create') as f:
            serializers.MediaItemSerializer().create(validated_data={})
        f.assert_called()

        request = mock.MagicMock()
        request.user.is_anonymous = False
        request.user.username = 'testuser'
        with mock.patch('mediaplatform.models.MediaItem.objects.create_for_user') as f:
            serializers.MediaItemSerializer(context={'request': request}).create(validated_data={})
        f.assert_called()


class ChannelSerializerTestCase(TestCase):
    def test_create(self):
        with mock.patch('mediaplatform.models.Channel.objects.create') as f:
            serializers.ChannelSerializer().create(validated_data={})
        f.assert_called()

        request = mock.MagicMock()
        request.user.is_anonymous = False
        request.user.username = 'testuser'
        with mock.patch('mediaplatform.models.Channel.objects.create_for_user') as f:
            serializers.ChannelSerializer(context={'request': request}).create(validated_data={})
        f.assert_called()


class MediaItemRelatedChannelIdField(TestCase):
    fixtures = ['api/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        self.patch_get_person()
        self.item = mpmodels.MediaItem.objects.get(id='empty')
        self.user = get_user_model().objects.first()
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.crsids.append(self.user.username)
        self.item.channel.edit_permission.save()

    def test_no_context_queryset(self):
        """If there is no context, an empty queryset is returned."""
        serialiser = serializers.MediaItemSerializer(data={
            'title': 'test', 'channelId': self.item.channel.id
        })
        self.assertFalse(serialiser.is_valid())

    def test_no_request_queryset(self):
        """If there is no request, an empty queryset is returned."""
        serialiser = serializers.MediaItemSerializer(data={
            'title': 'test', 'channelId': self.item.channel.id
        }, context={})
        self.assertFalse(serialiser.is_valid())

    def test_request_with_user_queryset(self):
        """If there is a request, the channel is in the queryset."""
        request = APIRequestFactory().get('/')
        request.user = self.user
        serialiser = serializers.MediaItemSerializer(data={
            'title': 'test', 'channelId': self.item.channel.id
        }, context={'request': request})
        self.assertTrue(serialiser.is_valid())

    def test_request_with_non_edit_user_queryset(self):
        """If there is a request but for a user without edit permissions, the channel is not in the
        queryset.

        """
        request = APIRequestFactory().get('/')
        request.user = AnonymousUser()
        serialiser = serializers.MediaItemSerializer(data={
            'title': 'test', 'channelId': self.item.channel.id
        }, context={'request': request})
        self.assertFalse(serialiser.is_valid())

    def patch_get_person(self):
        self.get_person_patcher = mock.patch('automationlookup.get_person')
        self.get_person = self.get_person_patcher.start()
        self.get_person.return_value = {
            'institutions': [{'instid': 'UIS'}],
            'groups': [{'groupid': '12345', 'name': 'uis-members'}]
        }
        self.addCleanup(self.get_person_patcher.stop)
