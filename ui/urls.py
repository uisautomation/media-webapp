"""
Default URL patterns for the :py:mod:`ui` application are provided by the :py:mod:`.urls` module.
You can use the default mapping by adding the following to your global ``urlpatterns``:

.. code::

    from django.urls import path, include

    urlpatterns = [
        # ...
        path('', include('ui.urls')),
        # ...
    ]

"""
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'ui'

with open(os.path.join(settings.BASE_DIR, 'CHANGELOG.md')) as fobj:
    changelog = fobj.read()

urlpatterns = [
    path(
        'media/new',
        login_required(TemplateView.as_view(template_name="ui/media_item_new.html")),
        name='media_item_new'
    ),
    path('media/<slug:pk>/analytics', views.MediaItemAnalyticsView.as_view(),
         name='media_item_analytics'),
    path('media/<slug:pk>/edit', views.MediaView.as_view(), name='media_item_edit'),
    path('media/<slug:pk>', views.MediaView.as_view(), name='media_item'),
    path('media/<slug:pk>.rss', views.MediaItemRSSView.as_view(), name='media_item_rss'),
    path('channels/<pk>', views.ChannelView.as_view(), name='channel'),
    path(
        'playlists/new',
        login_required(TemplateView.as_view(template_name="ui/playlist_new.html")),
        name='playlist_new'
    ),
    path('playlists/<slug:pk>', views.PlaylistView.as_view(), name='playlist'),
    path('playlists/<slug:pk>.rss', views.PlaylistRSSView.as_view(), name='playlist_rss'),
    path('playlists/<slug:pk>/edit', views.PlaylistView.as_view(), name='playlist_edit'),
    path('about', TemplateView.as_view(template_name="ui/about.html"), name='about'),
    path('changelog', TemplateView.as_view(
        template_name="ui/changelog.html", extra_context={'changelog': changelog}
    ), name='changelog'),
    path('', TemplateView.as_view(template_name="index.html"), name='home'),
]
