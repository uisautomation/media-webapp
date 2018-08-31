The Web App Project
===================

The ``mediawebapp`` project contains top-level configuration and URL routes for
the entire web application.

Settings
--------

The ``mediawebapp`` project ships a number of settings files.

.. _settings:

Generic settings
````````````````

.. automodule:: mediawebapp.settings
    :members:

.. _settings_testsuite:

Test-suite specific settings
````````````````````````````

.. automodule:: mediawebapp.settings.tox
    :members:

.. _settings_developer:

Developer specific settings
```````````````````````````

.. automodule:: mediawebapp.settings.developer
    :members:

Custom test suite runner
------------------------

The :any:`test suite settings <settings_testsuite>` overrides the
``TEST_RUNNER`` setting to point to
:py:class:`~mediawebapp.test.runner.BufferedTextTestRunner`. This runner captures
output to stdout and stderr and only reports the output if a test fails. This
helps make our tests a little less noisy.

.. autoclass:: mediawebapp.test.runner.BufferedDiscoverRunner

.. autoclass:: mediawebapp.test.runner.BufferedTextTestRunner
