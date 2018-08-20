from django.test import TestCase


class SitemapTestCase(TestCase):
    def test_sitemap_render(self):
        "A sitemap is available at /sitemap.xml"
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
