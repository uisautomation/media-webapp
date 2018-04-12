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

from django.urls import path

from . import views

app_name = 'smsjwplatform'
urlpatterns = [
    path('embed/<int:media_id>/', views.embed, name='embed'),
    path('rss/media/<int:media_id>/', views.rss_media, name='rss_media'),
]
