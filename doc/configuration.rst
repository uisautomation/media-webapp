Configuration
-------------

This section describes any settings which are specific to the Streaming Media
Service application.

.. _database-config:

Specifying the database
```````````````````````

The default ``settings.py`` file contains a facility to configure the database
by means of environment variables. A variable with a name of the form
``DJANGO_DB_<key>`` will be used to set the ``DATABASES['default'][<key>]``
setting. So, for example, one could set the location of the sqlite database by
setting the ``DJANGO_DB_NAME`` environment variable or one could change the
backend by setting ``DJANGO_DB_BACKEND``.

Default settings
````````````````

The default settings are given in the :py:mod:`smswebapp.settings.base` module:

.. automodule:: smswebapp.settings.base
    :members:
    :member-order: bysource
