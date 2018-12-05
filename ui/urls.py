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
        login_required(TemplateView.as_view(template_name="index.html")),
        name='media_item_new'
    ),
    path('media/<slug:pk>/analytics', views.MediaView.as_view(), name='media_item_analytics'),
    path('media/<slug:pk>/edit', views.MediaView.as_view(), name='media_item_edit'),
    path('media/<slug:pk>', views.MediaView.as_view(), name='media_item'),
    path('media/<slug:pk>.rss', views.MediaItemRSSView.as_view(), name='media_item_rss'),
    path(
        'media/<slug:pk>/jwp', views.MediaItemJWPlayerConfigurationView.as_view(), name='media_jwp'
    ),
    # The embed view has no 404 - it simply displays an error if the media cannot be found.
    path(
        'media/<slug:pk>/embed', TemplateView.as_view(template_name="index.html"),
        name='media_embed'
    ),
    path('channels/<pk>', views.ChannelView.as_view(), name='channel'),
    path(
        'playlists/new',
        login_required(TemplateView.as_view(template_name='index.html')),
        name='playlist_new'
    ),
    path('playlists/<slug:pk>', views.PlaylistView.as_view(), name='playlist'),
    path('playlists/<slug:pk>.rss', views.PlaylistRSSView.as_view(), name='playlist_rss'),
    path('playlists/<slug:pk>/edit', views.PlaylistView.as_view(), name='playlist_edit'),
    path(
        'playlists/<slug:pk>/embed', TemplateView.as_view(template_name="index.html"),
        name='playlist_embed'
    ),
    path(
        'playlists/<slug:pk>/jwp', views.PlaylistJWPlayerConfigurationView.as_view(),
        name='playlist_jwp'
    ),

    # Static text page UI views. If many more static pages are added in future, we will want to
    # think about a helper function for creating these paths.
    path('about', TemplateView.as_view(template_name="index.html"), name='about'),
    path('changelog', TemplateView.as_view(template_name="index.html"), name='about'),

    # Static text page content views. If many more static pages are added in future, we will want
    # to think about a helper function for creating these paths.
    path('about.md', TemplateView.as_view(
        template_name='ui/about.md', content_type='text/markdown; charset=UTF-8'
    ), name='about'),
    path('changelog.md', TemplateView.as_view(
        template_name="ui/changelog.md", content_type='text/markdown; charset=UTF-8',
        extra_context={'changelog': changelog}
    ), name='changelog_markdown'),

    path('', TemplateView.as_view(template_name="index.html"), name='home'),
    path('search', TemplateView.as_view(template_name="index.html"), name='search'),

    # A pre-configured JWPlayer library.
    path('lib/player.js', views.PlayerLibraryView.as_view(), name='player_lib'),
]
