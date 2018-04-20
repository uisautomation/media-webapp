"""
URL routing schema for Support for Legacy SMS.

"""

from django.urls import path

from . import views

app_name = "legacy-sms"

urlpatterns = [
    # remove this once legacy SMS has the new redirect rule
    path('embed/<int:media_id>/', views.embed),

    path('media/<int:media_id>/embed', views.embed, name='embed'),
    path('rss/media/<int:media_id>/', views.rss_media, name='rss_media'),
]
