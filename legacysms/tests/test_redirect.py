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


@override_settings(
    LEGACY_SMS_REDIRECT_FORMAT='{url.scheme}://test.{url.netloc}{url.path}',
    LEGACY_SMS_DOWNLOADS_URL='https://downloads.invalid/'
)
class DownloadTests(TestCase):
    def test_basic_media_download(self):
        """A simple media download redirect should produce the correct result."""
        self.assertRedirects(
            redirect.media_download(1234, 5678, 'mp4'),
            'https://test.downloads.invalid/1234/5678.mp4',
            fetch_redirect_response=False)

    def test_requires_integer_media_id(self):
        """Passing non-integer media id raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_download('some/malicious/path', 5768, 'mp4')

    def test_requires_integer_clip_id(self):
        """Passing non-integer clip id raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_download(1234, 'some/malicious/path', 'mp4')


@override_settings(
    LEGACY_SMS_REDIRECT_FORMAT='{url.scheme}://test.{url.netloc}{url.path}',
    LEGACY_SMS_FRONTEND_URL='https://sms.invalid/'
)
class MediaPageTests(TestCase):
    def test_basic_redirect(self):
        """A simple redirect should produce the correct result."""
        self.assertRedirects(
            redirect.media_page(1234), 'https://test.sms.invalid/media/1234',
            fetch_redirect_response=False)

    def test_requires_integer(self):
        """Passing non-integer raises an error."""
        with self.assertRaises(ValueError):
            redirect.media_page('some/malicious/path')
