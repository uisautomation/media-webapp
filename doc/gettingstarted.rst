Getting started
===============

This section is a guide to checking out the source and getting a development
machine configured. More information on development is found in the
:doc:`Developer's guide <developer>`.

Fork the upstream repository
````````````````````````````

The repository at https://github.com/uisautomation/sms-webapp is configured to
disallow pushing to master. You'll need to *fork* the repository into your
personal account and then open pull requests from your personal repository into
the main repository.

Set up cloud integrations
`````````````````````````

Visit the following cloud tool sites, sign in with GitHub and add your new
fork:

1. Add your repository to  `Travis CI <https://travis-ci.org/>`_.
2. Go to `Codecov <https://codecov.io/>`_ and add your fork as a watched repo.
   Make sure to enable the Codecov integration.

Clone the repository locally
````````````````````````````

Clone the remote upstream repository locally and configure the push URL to be
your local user fork. This means that ``git push`` commands will modify your
local fork but ``git pull`` commands will automatically fetch from the upstream
repository.

.. code-block:: bash

    $ git clone git@github.com:uisautomation/sms-webapp.git
    $ cd sms-webapp
    $ git remote set-url origin --push git@github.com:$USER/sms-webapp.git

.. note::

    Make sure to replace ``$USER`` with your GitHub user name. If your
    GitHub user name happens to be the same as your local user name, on
    Unix-y systems this will be done by magic!

It is also worth setting up an explicit remote for your personal repository.
Sometimes you'll want to ``push`` or ``pull`` from it.

.. code-block:: bash

    $ git remote add $USER git@github.com:$USER/sms-webapp.git

Install docker-compose
``````````````````````

In order to bring up a development web server or to run tests, you will need
docker-compose installed. `Installation instructions
<https://docs.docker.com/compose/install/>`_ are available on Docker's site.

Run tests
`````````

Once docker-compose is installed, you can run the tests using the ``compose.sh``
wrapper script:

.. code-block:: bash

    $ ./compose.sh tox run --rm tox

Configure secrets
`````````````````

Secrets used in development are loaded from a ``secrets.env`` file in the
project root. An example of this file is located at ``secrets.env.in``. Copy it
to ``secrets.env`` and fill in the appropriate secrets. ``secrets.env`` has been
added to the ``.gitignore`` file to guard against accidentally committing the
file.

Bring up a development web-server
`````````````````````````````````

If the tests pass, you should be able to bring up a development web-server:

.. code-block:: bash

    $ ./compose.sh development

The application should now be available at http://localhost:8000/.

.. note::

    Some settings are loaded from environment variables. These are settings
    which are either sensitive or dependent on third-party sources.
    Docker-compose will warn when starting the server if these variables are not
    set. These secrets are loaded by the docker-compose configuration from a
    file named ``secrets.env`` which must be created. See the ``secrets.env.in``
    file for guidance. ``secrets.env`` has been added to the ``.gitignore`` file
    to guard agains inadvertently commiting it.

Next steps
``````````

See the :doc:`developer` for what to do next.
