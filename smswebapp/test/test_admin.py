"""
Test that the admin pages are available and protected.

"""
from urllib.parse import urljoin
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase


class AdminTests(TestCase):
    def setUp(self):
        # create superuser
        self.superuser = User.objects.create_superuser(
            'test0001', 'test@example.com', '')

    def test_unauthenticated(self):
        """Unauthenticated log in to admin redirects to login."""
        r = self.client.get(reverse('admin:index'))
        # We really should use urlencode here to escape "/" characters in the
        # admin:index view URL. However, it would appear that the admin doesn't
        # so if we do, the test fails :(.
        expected_url = urljoin(reverse('admin:login'),
                               '?next=' + reverse('admin:index'))
        self.assertRedirects(r, expected_url, target_status_code=200)

    def test_authenticated(self):
        """Authenticated log in to admin as superuser succeeds."""
        self.client.force_login(self.superuser)
        r = self.client.get(reverse('admin:index'))
        self.assertEqual(r.status_code, 200)
