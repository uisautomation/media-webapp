"""
URL routing schema for Support for Legacy SMS.

"""

from django.urls import path

from . import views

app_name = "legacy-sms"

urlpatterns = [
    path('embed/<int:media_id>/', views.embed, name='embed'),
    path('rss/media/<int:media_id>/', views.rss_media, name='rss_media'),
]
