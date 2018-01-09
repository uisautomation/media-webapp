"""
Test that the registered system checks work as expected.

"""
from django.conf import settings
from django.core.management import call_command
# Q: is this a documented import location for SystemCheckError?
from django.core.management.base import SystemCheckError
from django.test import TestCase


class JWPlatformCreds(TestCase):
    """
    JWPlatform API credentials are checked for their presence.

    """
    def test_checks_pass(self):
        """The system checks should succeed in the test suite configuration."""
        self.assertNotEqual(settings.JWPLATFORM_API_KEY, '')
        self.assertNotEqual(settings.JWPLATFORM_API_SECRET, '')
        call_command('check')

    def test_api_key_required(self):
        """The JWPLATFORM_API_KEY setting must be non-blank."""
        with self.settings(JWPLATFORM_API_KEY=''):
            with self.assertRaises(SystemCheckError):
                call_command('check')

    def test_api_secret_required(self):
        """The JWPLATFORM_API_SECRET setting must be non-blank."""
        with self.settings(JWPLATFORM_API_SECRET=''):
            with self.assertRaises(SystemCheckError):
                call_command('check')
