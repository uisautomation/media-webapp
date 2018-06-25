"""
WSGI config for smswebapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smswebapp.settings")

application = get_wsgi_application()

# Only *after* the application is initialised above will the Django settings be available.
from django.conf import settings  # noqa: E402

whitenoise_params = {}

if settings.DEBUG:
    # In development (when DEBUG is True), enable the whitenoise autorefresh feature which will
    # check if the file has updated on disk before responding.
    whitenoise_params['autorefresh'] = True

application = WhiteNoise(
    application,
    root=settings.FRONTEND_APP_BUILD_DIR, prefix='/',
    index_file=True,
    **whitenoise_params,
)
