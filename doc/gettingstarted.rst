Getting started
===============

Fork the upstream repository
````````````````````````````

The repository at https://bitbucket.org/uisautomation/sms-webapp is configured
to disallow opening new branches by default. You'll need to *fork* the
repository into your personal account and then open pull requests from your
personal repository into the main repository.

.. seealso::

    Bitbucket has `documentation on hot to fork a repository
    <https://confluence.atlassian.com/bitbucket/forking-a-repository-221449527.html>`_
    which can be followed.


Clone the repository locally
````````````````````````````

Clone the remote upstream repository locally and configure the push URL to be
your local user fork. This means that ``git push`` commands will modify your
local fork but ``git pull`` commands will automatically fetch from the upstream
repository.

.. code:: bash

    $ git clone git@bitbucket.org:uisautomation/sms-webapp.git
    $ cd sms-webapp
    $ git remote set-url origin --push git@bitbucket.org:$USER/sms-webapp.git

Run the test suite
``````````````````

The `tox <https://tox.readthedocs.io/>`_ automation tool is used to run tests
inside their own virtualenv. This way we can be sure that we know which packages
are required to run the tests. By default tests are run in a sqlite database
within a per-environment temporary directory. Other databases can be used by
setting the ``DJANGO_DB_...`` environment variables. See :any:`database-config`.

Perform initial migration
`````````````````````````

Before running for the first time, an initial database migration must be
performed as usual:

.. code:: bash

    $ ./manage.py migrate

Run the development server
``````````````````````````

The development web server may now be run:

.. code:: bash

    $ ./manage.py runserver

