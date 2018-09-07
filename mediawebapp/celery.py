from __future__ import absolute_import, unicode_literals

import logging
import os

from celery import Celery

LOG = logging.getLogger(__name__)

# Make sure that Django's settings module configuration is present.
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    raise RuntimeError('DJANGO_SETTINGS_MODULE environment variable is unset')

app = Celery('proj')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True, name='mediawebapp.debug')
def debug_task(self, *args, **kwargs):
    """A debugging task which simply logs the request and its arguments."""
    LOG.info('Debug task.\nRequest: %r\nArgs: %r\nKeyword args: %r', self, args, kwargs)
    print('Request: {0!r}'.format(self.request))
