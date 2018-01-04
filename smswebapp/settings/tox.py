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
