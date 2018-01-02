"""
Test basic functionality of project-specific views.

"""
from django.test import TestCase


class IndexTest(TestCase):
    def test_index(self):
        """GET-ing / should succeed."""
        r = self.client.get('')
        self.assertEqual(r.status_code, 200)
