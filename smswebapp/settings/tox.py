"""
The :py:mod:`smswebapp.settings_testsuite` module contains settings which are
specific to the test suite environment. The default ``tox`` test environment
uses this settings module when running the test suite.

"""
import copy
import json
import os

# Import settings from the base settings file
from .base import *  # noqa: F401, F403


#: The default test runner is changed to one which captures stdout and stderr
#: when running tests.
TEST_RUNNER = 'smswebapp.test.runner.BufferedDiscoverRunner'

#: Static files are collected into a directory determined by the tox
#: configuration. See the tox.ini file.
STATIC_ROOT = os.environ.get('TOX_STATIC_ROOT')

# When running under tox, it is useful to see the database config. Make a deep copy and censor the
# password.
_db_copy = copy.deepcopy(DATABASES)  # noqa: F405
for v in _db_copy.values():
    if 'PASSWORD' in v:
        v['PASSWORD'] = '<redacted>'
print('Databases:')
print(json.dumps(_db_copy, indent=2))

#: When running the test suite, we do not call any external APIs but we *do* check that the
#: ``JWPLATFORM_...`` settings must be set.
JWPLATFORM_API_KEY = 'xxx-not-a-key-xxx'
JWPLATFORM_API_SECRET = '+++-not-a-secret-+++'

#: Use a fake player key for embedding.
JWPLATFORM_EMBED_PLAYER_KEY = 'someplayer'

SMS_OAUTH2_CLIENT_ID = 'xxx-not-an-id-xxx'
SMS_OAUTH2_CLIENT_SECRET = '+++-not-a-secret-+++'
SMS_OAUTH2_TOKEN_URL = 'http://oauth2.invalid/auth'
LOOKUP_ROOT = 'http://lookup.invalid/'
SMS_OAUTH2_LOOKUP_SCOPES = 'not-a-lookup-scope'

#: Be less verbose in logging with tox
LOGGING = None
