from django.test import TestCase
from django.urls import reverse


class ExampleTests(TestCase):
    def test_get(self):
        r = self.client.get(reverse('legacysms:example'))
        self.assertEqual(r.status_code, 200)
