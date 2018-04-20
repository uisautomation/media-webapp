Support for Legacy SMS
===============================================================================

Apache Configuration
````````````````````

This application implements views emulating views on the legacy SMS system. It
is intended that emulated views may be redirected directly to this application
using Apache configuration similar to the following:

.. code:: apache

    # Redirect configuration for offloading onto the new SMS provider.
    RewriteEngine On

    # If necessary, enable debugging support by uncommenting these lines:
    # RewriteLog "/var/log/apache2/rewrite.log"
    # RewriteLogLevel 3

    # Requests which are passed on to new provider can use the URL path
    # directly.
    RewriteRule "^/media/(.*)/embed/?$" "https://ump.uis.cam.ac.uk/legacy$0" [L]

    # Handle any requests passed back the legacy application by the new
    # provider. Download requests are passed on to the download server which has
    # a similar Apache configuration to handle _legacy URLs.
    RewriteRule "^/_legacy/_downloads/(.*)$" "https://downloads.sms.cam.ac.uk/_legacy/$0" [L]
    RewriteRule "^/_legacy/(.*)$" "/$1" [PT,L]

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

Redirection back to legacy SMS
``````````````````````````````

.. automodule:: legacysms.redirect
    :members:

Settings
````````

.. automodule:: legacysms.defaultsettings
    :members:
    :member-order: bysource

Application configuration
`````````````````````````

.. automodule:: legacysms.apps
    :members:
