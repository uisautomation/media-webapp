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

    The CircleCI job runs tox configured with a PostgreSQL database to match
    that deployed in production. To replicate this, either run a PostgreSQL
    instance on the local machine, use the Google Cloud SQL proxy or :any:`run
    the tests via docker-compose <docker-tox>`.

.. _devserver:

Run the development server
``````````````````````````

Django comes with a development web server which can be run via:

.. code-block:: bash

    $ ./manage.py runserver

The server should now be browsable at http://localhost:8000/.

Docker images
-------------

The application is :any:`deployed <deployment>` using `Docker
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

    $ docker-compose run migrate

To run the development server:

.. code-block:: bash

    $ docker-compose up devserver

This makes use of the :py:class:`smswebapp.settings.developer` settings,
launches a PostgreSQL container for the development server and a `MailHog
<https://github.com/mailhog/MailHog>`_ server to monitor outgoing email. The web
app is available at http://localhost:8000/ and the MailHog instance at
http://localhost:8025/.

.. note::

    If the ``requirements.txt`` file is modified, you'll need to re-build the
    container image via ``docker-compose build``.

Occasionally, it is useful to get an interactive Python shell which is set up to
be able to import the application code and to make database queries, etc. You
can launch such a shell via:

.. code-block:: bash

    $ docker-compose run shell

.. _docker-tox:

Running tests within the container
``````````````````````````````````

The test-suite can be run within the container using a PostgreSQL database in
the following way:

.. code-block:: bash

    $ docker-compose tox

.. note::

    Unlike the other docker-compose services, the tox service *does not* mount
    the local repository as a volume. This is because tox needs to write to the
    filesystem. Make sure that the container build is up to date via
    ``docker-compose build`` before running tests.

Cloud infrastructure
--------------------

This section provides a brief outline of cloud infrastructure for development.
:any:`deployment` provides a discussion of the cloud infrastructure used for
*deployment*.

Source control
``````````````

The panel is hosted on GitHub at https://github.com/uisautomation/sms-webapp.
The repository has ``master`` set up to be writeable only via pull request. It
is intended that local development happens in personal forks and is merged via
pull request. The main rationale for this is a) it guards against accidentally
``git push``-ing the wrong branch and b) it reduces the number of "dangling"
branches in the main repository.

.. _circleci:

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
* By logging into CircleCI via GitHub, you can enable CircleCI for your
  personal fork. This is **highly recommended** as you'll get rapid feedback via
  email if you push a commit to a branch which does not pass the test suite.

.. note::

    In order to better match production, CircleCI is set up to run unit tests
    using the PostgreSQL database and *not* sqlite. If you only run unit tests
    locally with sqlite then it is possible that some tests may fail.

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

This documentation is re-built on each commit to master by
`Read the Docs <https://readthedocs.org/>`_. It is hosted at
https://uis-smswebapp.readthedocs.io/en/latest/.

