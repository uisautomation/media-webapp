"""
Test redirects back to legacy SMS.

"""
from .. import redirect

from django.conf import settings
from django.test import TestCase, override_settings


@override_settings(LEGACY_SMS_REDIRECT_BASE_URL='http://legacysms.invalid/a/b/')
class RedirectTestCase(TestCase):
    """
    Base class for test cases testing redirect behaviour. This cannot be a mixin since it uses the
    override_settings decorator.

    """

    def assert_is_redirect_to_path(self, response, expected_path):
        """
        Check that the response is a redirect to the specified path relative to the
        LEGACY_SMS_REDIRECT_BASE_URL setting.

        """
        self.assertEqual(response.status_code, 302)
        location = response['Location']
        self.assertTrue(location.startswith(settings.LEGACY_SMS_REDIRECT_BASE_URL))
        path = location[len(settings.LEGACY_SMS_REDIRECT_BASE_URL):]
        self.assertEqual(path, expected_path)


class MediaEmbedTests(RedirectTestCase):
    def test_basic_redirect(self):
        """A simple redirect should produce the correct result."""
        self.assert_is_redirect_to_path(redirect.media_embed(1234), 'media/1234/embed')

    def test_requires_integer(self):
        """Passing non-integer raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_embed('some/malicious/path')


class RSSTests(RedirectTestCase):
    def test_basic_media_redirect(self):
        """A simple media item redirect should produce the correct result."""
        self.assert_is_redirect_to_path(redirect.media_rss(1234), 'rss/media/1234')

    def test_requires_integer(self):
        """Passing non-integer raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_rss('some/malicious/path')
