Developer's guide
=================

This section contains information on how to perform various task and an overview
of how our development infrastructure is set up.

Local development
-----------------

These tasks are usually performed on an individual developer's machine.

.. _run-tests:

Run the test suite
``````````````````

The `tox <https://tox.readthedocs.io/>`_ automation tool is used to run tests
inside their own virtualenv. This way we can be sure that we know which packages
are required to run the tests. By default tests are run in a sqlite database
within a per-environment temporary directory. Other databases can be used by
setting the ``DJANGO_DB_...`` environment variables. See :any:`database-config`.

.. code-block:: bash

    $ tox

By default, ``tox`` will run the test suite using the version of Python used
when we deploy and will compile a local version of the documentation. The ``-e``
flag may be used to explicitly specify an environment to run. For example, to
build only the documentation:

.. code-block:: bash

    $ tox -e doc

.. note::

    The Travis CI job runs tox configured with a PostgreSQL database to match
    that deployed in production. To replicate this, either run a PostgreSQL
    instance on the local machine, use the Google Cloud SQL proxy or :any:`run
    the tests via docker-compose <docker-tox>`.

.. _toxenvs:

tox environments
````````````````

The following tox environments are available.

py36
    Run by default. Launch the test suite under Python 3.6. Generate a
    code-coverage report and display a summary coverage report.

doc
    Run by default. Build documentation and write it to the ``build/doc/``
    directory.

flake8
    Run by default. Check for code-style violations using the `flake8
    <http://flake8.pycqa.org/>`_ linter.

collectstatic
    Collect static files used by Django to the ``build/static/`` directory.

.. _devserver:

Run the development server
``````````````````````````

Django comes with a development web server which can be run via:

.. code-block:: bash

    $ ./manage.py runserver 0.0.0.0:8080

The server should now be browsable at http://localhost:8080/.

Building the documentation
``````````````````````````

This documentation may be built using the "doc" :any:`tox environment
<toxenvs>`.

Docker images
-------------

The application is deployed using `Docker
<https://docker.com/>`_ containers on the Google Container Engine. Usually one
can just use the :any:`local development server <devserver>` to develop the
application but occasionally one needs to test the container or make use of the
same PostgreSQL database which is used in production.

.. _docker-devserver:

Running a development server within the container
`````````````````````````````````````````````````

There is a `docker-compose <https://docs.docker.com/compose/>`_ file at the
top-level of the webapp repository which contains configuration allowing the
application container to be launched in a development mode. In this mode the
application repository is mounted **read-only** as a volume within the container
over the top of the application code so changes are reflected within the
container without need to rebuild it.

The local repository is mounted read-only because any files written by the
application will appear in the local repository as a root-owned file which can
be troublesome.

Before you bring the development server container up, run an initial database
migration:

.. code-block:: bash

    $ docker-compose run --rm migrate

To run the development server:

.. code-block:: bash

    $ docker-compose up devserver

This makes use of the :py:class:`smswebapp.settings.developer` settings,
launches a PostgreSQL container for the development server and a `MailHog
<https://github.com/mailhog/MailHog>`_ server to monitor outgoing email. The web
app is available at http://localhost:8080/ and the MailHog instance at
http://localhost:8025/.

.. note::

    If the ``requirements.txt`` file is modified, you'll need to re-build the
    container image via ``docker-compose build``.

Occasionally, it is useful to get an interactive Python shell which is set up to
be able to import the application code and to make database queries, etc. You
can launch such a shell via:

.. code-block:: bash

    $ docker-compose run --rm shell

.. _docker-tox:

Running tests within the container
``````````````````````````````````

The test-suite can be run within the container using a PostgreSQL database in
the following way:

.. code-block:: bash

    $ docker-compose run --rm tox

Cloud infrastructure
--------------------

This section provides a brief outline of cloud infrastructure for development.

Source control
``````````````

The panel is hosted on GitHub at https://github.com/uisautomation/sms-webapp.
The repository has ``master`` set up to be writeable only via pull request. It
is intended that local development happens in personal forks and is merged via
pull request. The main rationale for this is a) it guards against accidentally
``git push``-ing the wrong branch and b) it reduces the number of "dangling"
branches in the main repository.

.. _travisci:

Unit tests
``````````

The project is set up on `Travis CI <https://travis-ci.org/>`_ to automatically
run unit tests and build documentation on each commit to a branch and on each
pull request.

.. note::

    By logging into Travis CI via GitHub, you can enable Travis CI for your
    personal fork. This is **highly recommended** as you'll get rapid feedback
    via email if you push a commit to a branch which does not pass the test
    suite.

In order to better match production, Travis CI is set up to run unit tests using
the PostgreSQL database and *not* sqlite. If you only run unit tests locally
with sqlite then it is possible that some tests may fail.

Code-coverage
`````````````

Going to `CodeCov <https://codecov.io/>`_, logging in with GitHub and adding the
``sms-webapp`` repository will start code coverage reporting on pull-requests.

Documentation
`````````````

Travis CI has been set up so that when the master branch is built, the
documentation is deployed to https://uisautomation.github.io/sms-webapp via
GitHub pages. The `UIS robot <https://github.com/bb9e/>`_ machine account's
personal token is set up in Travis via the ``GITHUB_TOKEN`` environment
variable.

.. seealso::

    Travis CI's `documentation
    <https://docs.travis-ci.com/user/deployment/pages/>`_ on deploying to GitHub
    pages.

Code-style
``````````

The ``tox`` test runner will automatically check the code with `flake8
<http://flake8.pycqa.org/>`_ to ensure PEP8 compliance. Sometimes, however,
rules are made to be broken and so you may find yourself needing to use the
`noqa in-line comment
<http://flake8.pycqa.org/en/latest/user/violations.html#in-line-ignoring-errors>`_
mechanism to silence individual errors.

To run the flake8 tests manually, specify the tox environment:

.. code:: bash

    $ tox -e flake8

Documentation
`````````````

This documentation is re-built on each commit to master by Travis and posted to
GitHub pages at https://uisautomation.github.io/sms-webapp/.
