import os

from lookupproxy.settings.base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ['*']

OAUTH2_TOKEN_URL = os.environ.get('OAUTH2_TOKEN_URL')
OAUTH2_INTROSPECT_URL = os.environ.get('OAUTH2_INTROSPECT_URL')
OAUTH2_CLIENT_ID = os.environ.get('OAUTH2_CLIENT_ID')
OAUTH2_CLIENT_SECRET = os.environ.get('OAUTH2_CLIENT_SECRET')
OAUTH2_INTROSPECT_SCOPES = ['hydra.introspect']

SWAGGER_SETTINGS['SECURITY_DEFINITIONS']['oauth2']['authorizationUrl'] = (  # noqa: F405
    os.environ.get('OAUTH2_AUTH_URL')
)

# For the moment, the lookup certificates in test do not match the root hard-coded into the client.
LOOKUP_API_ENDPOINT_HOST = 'www.lookup.cam.ac.uk'

# Ensure that logging is shown in the console.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
