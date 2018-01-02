"""
Test basic functionality of project-specific views.

"""
from django.urls import reverse
from django.test import TestCase


class StatusTest(TestCase):
    def test_status(self):
        """GET-ing status page should succeed."""
        r = self.client.get(reverse('status'))
        self.assertEqual(r.status_code, 200)
