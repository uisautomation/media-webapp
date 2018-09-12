from django.test import TestCase

from ..celery import debug_task


class CeleryTestCase(TestCase):
    def test_debug_test(self):
        """The debug test should run without error."""
        debug_task()
