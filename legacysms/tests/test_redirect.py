"""
Test redirects back to legacy SMS.

"""
from django.test import TestCase, override_settings

from .. import redirect


@override_settings(
    LEGACY_SMS_REDIRECT_FORMAT='{url.scheme}://test.{url.netloc}{url.path}',
    LEGACY_SMS_FRONTEND_URL='https://sms.invalid/'
)
class MediaEmbedTests(TestCase):
    def test_basic_redirect(self):
        """A simple redirect should produce the correct result."""
        self.assertRedirects(
            redirect.media_embed(1234), 'https://test.sms.invalid/media/1234/embed',
            fetch_redirect_response=False)

    def test_requires_integer(self):
        """Passing non-integer raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_embed('some/malicious/path')


@override_settings(
    LEGACY_SMS_REDIRECT_FORMAT='{url.scheme}://test.{url.netloc}{url.path}',
    LEGACY_SMS_RSS_URL='https://rss.invalid/'
)
class RSSTests(TestCase):
    def test_basic_media_redirect(self):
        """A simple media item redirect should produce the correct result."""
        self.assertRedirects(
            redirect.media_rss(1234), 'https://test.rss.invalid/rss/media/1234',
            fetch_redirect_response=False)

    def test_requires_integer(self):
        """Passing non-integer raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_rss('some/malicious/path')
