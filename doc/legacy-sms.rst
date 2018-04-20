Support for Legacy SMS
===============================================================================

Installation
````````````

Add the ``legacysms`` application to your ``INSTALLED_APPS`` configuration as
usual and add the following to your URL configuration:

.. code::

    from django.urls import path

    # ...

    urlpatterns = [
        # ....
        path('legacy/', include('legacysms.urls', namespace='legacysms')),
        # ....
    ]

Views and serializers
`````````````````````

.. automodule:: legacysms.views
    :members:

Application configuration
`````````````````````````

.. automodule:: legacysms.apps
    :members:
