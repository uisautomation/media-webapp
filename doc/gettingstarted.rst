Getting started
===============

Fork the upstream repository
````````````````````````````

The repository at https://bitbucket.org/uisautomation/sms-webapp is configured
to disallow opening new branches by default. You'll need to *fork* the
repository into your personal account and then open pull requests from your
personal repository into the main repository.

.. seealso::

    Bitbucket has `documentation on how to fork a repository
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

.. note::

    Make sure to replace ``$USER`` with your bitbucket user name. If your
    bitbucket user name happens to be the same as your local user name, on
    Unix-y systems this will be done by magic!

It is also worth setting up an explicit remote for your personal repository.
Sometimes you'll want to ``push`` or ``pull`` from it.

.. code:: bash

    $ git remote add $USER git@bitbucket.org:$USER/sms-webapp.git

Install any requirements
````````````````````````

Usually you'll want to use the `tox <https://tox.readthedocs.io/>`_ automation
tool to run tests, etc but you can install the application within your
virtualenv which will also install any dependencies:

.. code:: bash

    $ pip install -r requirements.txt
    $ pip install -e .

The ``-e`` flag to ``pip`` will cause the install to use symlinks rather than
copying which allows for in-place modification of the source without having to
re-install.

Perform initial migration
`````````````````````````

Before running for the first time, an initial database migration must be
performed as usual:

.. code:: bash

    $ ./manage.py migrate

Next steps
``````````

See the :any:`developer` for what to do next.
