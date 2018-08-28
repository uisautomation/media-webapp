"""
Tests for :py:mod:acl
"""
from unittest import mock
import urllib.parse

from django.test import TestCase
from django.test.utils import override_settings

from mediaplatform_jwp import jwplatform as api
from mediaplatform_jwp import models


class JWPlatformTest(TestCase):
    """
    General module tests
    """

    def test_acl_parsing(self):
        models.CachedResource.objects.create(
            key='xyz', type=models.CachedResource.VIDEO,
            data={'key': 'xxx', 'custom': {'sms_acl': 'acl:WORLD,USER_mb2174:'}}
        )

        self.assertEqual(api.Video.from_key('xyz').acl, ['WORLD', 'USER_mb2174'])

    def test_corrupted_acl(self):
        models.CachedResource.objects.create(
            key='xyz', type=models.CachedResource.VIDEO,
            data={'key': 'xxx', 'custom': {'sms_acl': 'corrupted'}}
        )

        with self.assertRaises(ValueError):
            api.Video.from_key('xyz').acl


class PlatformDeliveryAPITests(TestCase):
    """
    Test pd_api_get() call.

    """
    def test_resource_must_start_with_slash(self):
        """The resource name must start with a slash."""
        with self.assertRaises(ValueError):
            api.pd_api_url('no/leading/slash')

    @override_settings(JWPLATFORM_API_SECRET='some-test-secret')
    def test_token_is_set(self):
        """A token is provided."""
        with mock.patch('time.time', return_value=123456):
            url_1 = api.pd_api_url('/example/resource')
            url_1_params = urllib.parse.parse_qs(urllib.parse.urlsplit(url_1).query)

            url_2 = api.pd_api_url('/example/resource', test_param='test')
            url_2_params = urllib.parse.parse_qs(urllib.parse.urlsplit(url_2).query)

        self.assertIn('token', url_1_params)
        self.assertIn('token', url_2_params)

        # The token depends only on resource name and current time so should be equal
        self.assertEqual(url_1_params['token'], url_2_params['token'])

        # We mock time.time() and JWPLATFORM_API_SECRET so we can check the token even if the
        # setting changes elsewhere.
        self.assertEqual(
            url_1_params['token'][0],
            ('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZXNvdXJjZSI6Ii9leGFtcGxlL3Jlc291cm'
             'NlIiwiZXhwIjoxMjcwODB9.9q_FIjKwckJ4yThXvfl6BWa0ObixoqKMa9HJbMAiciY'))

    def test_parameter_is_set(self):
        """Parameters are set on the URL."""
        url = api.pd_api_url('/example/resource', test_param1='test', test_param2=34)
        url_parts = urllib.parse.urlsplit(url)
        url_params = urllib.parse.parse_qs(url_parts.query)

        self.assertEqual(url_params['test_param1'], ['test'])
        self.assertEqual(url_params['test_param2'], ['34'])

    @override_settings(JWPLATFORM_API_BASE_URL='http://test.invalid/')
    def test_resource_is_fetched(self):
        """The URL path matches the resource."""
        url = api.pd_api_url('/example/resource', test_param1='test', test_param2=34)
        url_parts = urllib.parse.urlsplit(url)
        self.assertEqual(url_parts.scheme, 'http')
        self.assertEqual(url_parts.netloc, 'test.invalid')
        self.assertEqual(url_parts.path, '/example/resource')
