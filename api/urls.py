"""
URL routing schema for API

"""

from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('media/', views.MediaItemListView.as_view(), name='media_list'),
    path('media/<pk>', views.MediaItemView.as_view(), name='media_item'),
    path('media/<pk>/upload', views.MediaItemUploadView.as_view(), name='media_upload'),
    path('media/<pk>/analytics', views.MediaItemAnalyticsView.as_view(),
         name='media_item_analytics'),
    path('media/<pk>/embed', views.MediaItemEmbedView.as_view(), name='media_embed'),
    path('media/<pk>/source', views.MediaItemSourceView.as_view(), name='media_source'),
    path('media/<pk>/poster-<int:width>.<extension>',
         views.MediaItemPosterView.as_view(), name='media_poster'),
    path('channels/', views.ChannelListView.as_view(), name='channel_list'),
    path('channels/<pk>', views.ChannelView.as_view(), name='channel'),
    path('playlists/', views.PlaylistListView.as_view(), name='playlist_list'),
    path('playlists/<pk>', views.PlaylistView.as_view(), name='playlist'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
