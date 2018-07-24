from urllib.parse import urlparse

from django.test import TestCase

from mediaplatform import models as mpmodels

from .. import upload


class UploadTestCase(TestCase):
    fixtures = ['mediaplatform_jwp/tests/fixtures/mediaitems.yaml']

    def test_creates_endpoint(self):
        """Recording link data creates a correctly formatted endpoint."""
        item = mpmodels.MediaItem.objects.get(id='existing')
        link_data = {
            'protocol': 'http', 'address': 'example.invalid',
            'path': '/a/b/c', 'query': {'key': 'SOMEKEY', 'token': 'SOMETOKEN'},
        }
        upload.record_link_response(link_data, item)

        endpoint = mpmodels.UploadEndpoint.objects.get(item=item)
        for k in ['protocol', 'address', 'path']:
            self.assertIn(link_data[k], endpoint.url)
        for k in ['key', 'token']:
            self.assertIn(link_data['query'][k], endpoint.url)

        # URL should be parseable as a URL
        components = urlparse(endpoint.url)

        self.assertNotEqual(components.scheme, '')
        self.assertNotEqual(components.netloc, '')
        self.assertNotEqual(components.path, '')
