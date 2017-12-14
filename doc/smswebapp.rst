The Web App Project
===================

The ``smswebapp`` project contains top-level configuration and URL routes for
the entire web application.

Settings
--------

The ``smswebapp`` project ships a number of settings files.

.. _settings:

Generic settings
````````````````

.. automodule:: smswebapp.settings
    :members:

.. _settings_testsuite:

Test-suite specific settings
````````````````````````````

.. automodule:: smswebapp.settings_testsuite
    :members:

.. _settings_developer:

Developer specific settings
```````````````````````````

.. automodule:: smswebapp.settings_developer
    :members:

Custom test suite runner
------------------------

The :any:`test suite settings <settings_testsuite>` overrides the
``TEST_RUNNER`` setting to point to
:py:class:`~smswebapp.test.runner.BufferedTextTestRunner`. This runner captures
output to stdout and stderr and only reports the output if a test fails. This
helps make our tests a little less noisy.

.. autoclass:: smswebapp.test.runner.BufferedDiscoverRunner

.. autoclass:: smswebapp.test.runner.BufferedTextTestRunner
