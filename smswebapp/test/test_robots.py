from django.test import TestCase


class RobotsTxtTestCase(TestCase):
    def test_robots_txt_render(self):
        "A robots.txt is available"
        r = self.client.get('/robots.txt')
        self.assertEqual(r.status_code, 200)
