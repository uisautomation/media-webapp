Developer's guide
=================

This section contains information on how to perform various task and an overview
of how our development infrastructure is set up.

Local development
-----------------

These tasks are usually performed on an individual developer's machine.

.. run-tests:

Run the test suite
``````````````````

The `tox <https://tox.readthedocs.io/>`_ automation tool is used to run tests
inside their own virtualenv. This way we can be sure that we know which packages
are required to run the tests. By default tests are run in a sqlite database
within a per-environment temporary directory. Other databases can be used by
setting the ``DJANGO_DB_...`` environment variables. See :any:`database-config`.

Run the development server
``````````````````````````

Django comes with a development web server which can be run via:

.. code:: bash

    $ ./manage.py runserver

The server should now be browsable at http://localhost:8000/.

Cloud infrastructure
--------------------

This section provides a brief outline of cloud infrastructure for development.

Source control
``````````````

The panel is hosted on bitbucket at
https://bitbucket.org/uisautomation/sms-webapp. The repository has all branches
set up to be writeable only via pull request. It is intended that local
development happens in `personal forks
<https://confluence.atlassian.com/bitbucket/forking-a-repository-221449527.html>`_
and is merged via pull request. The main rationale for this is a) it guards
against accidentally ``git push``-ing the wrong branch and b) it reduces the
number of "dangling" branches in the main repository.

Unit tests
``````````

The project is set up on `CircleCI <https://circleci.com/>`_ to automatically
run unit tests and build documentation on each commit to a branch and on each
pull request. Some items to note:

* The `project dashboard
  <https://circleci.com/bb/uisautomation/sms-webapp>`_ on CircleCI lists all
  builds.
* Individual builds save two artifacts: a HTML code-coverage report and a build
  copy of the documentation. Both may be viewed from the "artifacts" tab on an
  individual build's page.
* By logging into CircleCI via bitbucket, you can enable CircleCI for your
  personal fork. This is **highly recommended** as you'll get rapid feedback via
  email if you push a commit to a branch which does not pass the test suite.

.. note::

    In order to better match production, CircleCI is set up to run unit tests
    using the PostgreSQL database and *not* sqlite. If you only run unit tests
    locally with sqlite then it is possible that some tests may fail.

Documentation
`````````````

This documentation is re-built on each commit to master by
`Read the Docs <https://readthedocs.org/>`_. It is hosted at
https://uis-smswebapp.readthedocs.io/en/latest/.

