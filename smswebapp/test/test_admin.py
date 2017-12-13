"""
Test that the admin pages are available and protected.

"""
from urllib.parse import urlparse
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
        self.assertEqual(r.status_code, 302)
        self.assertEqual(urlparse(r['Location']).path, reverse('admin:login'))

    def test_authenticated(self):
        """Authenticated log in to admin as superuser succeeds."""
        self.client.force_login(self.superuser)
        r = self.client.get(reverse('admin:index'))
        self.assertEqual(r.status_code, 200)
