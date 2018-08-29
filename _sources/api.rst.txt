REST API
========

The :py:mod:`api` module implements a REST-ful API for the media service based
on the `Django REST Framework <https://www.django-rest-framework.org/>`_.

Installation
------------

Add ``api`` to the ``INSTALLED_APPS`` setting and then update your
``urlpatterns`` as follows:

.. code::

    urlpatterns = [
        # ...
        path('api/', include('api.urls', namespace='api')),
        # ...
    ]

Views
-----

.. automodule:: api.views
    :members:
    :member-order: bysource

Serializers
-----------

.. automodule:: api.serializers
    :members:
    :member-order: bysource
