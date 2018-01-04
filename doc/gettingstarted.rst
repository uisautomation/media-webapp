Getting started
===============

This section is a guide to checking out the source and getting a development
machine configured. More information on development is found in the
:any:`Developer's guide <developer>`.

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
1. Go to `Codecov <https://codecov.io/>`_ and add your fork as a watched repo.
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
    bitbucket user name happens to be the same as your local user name, on
    Unix-y systems this will be done by magic!

It is also worth setting up an explicit remote for your personal repository.
Sometimes you'll want to ``push`` or ``pull`` from it.

.. code-block:: bash

    $ git remote add $USER git@github.com:$USER/sms-webapp.git

Install any requirements
````````````````````````

Usually you'll want to use the `tox <https://tox.readthedocs.io/>`_ automation
tool to run tests, etc but you can install the application within your
virtualenv which will also install any dependencies:

.. code-block:: bash

    $ pip install -r requirements.txt
    $ pip install -e .

The ``-e`` flag to ``pip`` will cause the install to use symlinks rather than
copying which allows for in-place modification of the source without having to
re-install.

Perform initial migration
`````````````````````````

Before running for the first time, an initial database migration must be
performed as usual:

.. code-block:: bash

    $ ./manage.py migrate

Next steps
``````````

See the :any:`developer` for what to do next.
