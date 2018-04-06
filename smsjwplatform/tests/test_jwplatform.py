"""
Tests for :py:mod:acl
"""
from unittest import mock

from django.test import TestCase

from smsjwplatform.jwplatform import get_acl


class JWPlatformTest(TestCase):
    """
    General module tests
    """

    def test_get_acl(self):

        client = mock.Mock()

        client.videos.show.return_value = {
            'video' : {'custom': {'sms_acl': 'acl:WORLD,USER_mb2174:'}}
        }
        self.assertEqual(get_acl(123, client=client), ['WORLD', 'USER_mb2174'])

        client.videos.show.assert_called_with(video_key=123)

        client.videos.show.return_value = {
            'video' : {'custom': {'sms_acl': 'corrupted'}}
        }

        with self.assertRaises(ValueError):
            get_acl(123, client=client)
