"""
The :py:mod:`smswebapp.settings_testsuite` module contains settings which are
specific to the test suite environment. The default ``tox`` test environment
uses this settings module when running the test suite.

"""
# Import settings from the base settings file
from .settings import *  # noqa: F401, F403


#: The default test runner is changed to one which captures stdout and stderr
#: when running tests.
TEST_RUNNER = 'smswebapp.test.runner.BufferedDiscoverRunner'
