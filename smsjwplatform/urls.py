"""
Default URL patterns for the :py:mod:`smsjwplatform` application are provided by the
:py:mod:`.urls` module. You can use the default mapping by adding the following to your global
``urlpatterns``:

.. code::

    from django.urls import path, include

    urlpatterns = [
        # ...
        path('sms/', include('smsjwplatform.urls')),
        # ...
    ]

"""

app_name = 'smsjwplatform'
urlpatterns = []
