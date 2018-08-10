"""
URL routing schema for API

"""

from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import views

app_name = 'api'

schema_view = get_schema_view(
   openapi.Info(
      title='Media API',
      default_version='v1',
      description='Media Service Content API',
      contact=openapi.Contact(email='automation@uis.cam.ac.uk'),
      license=openapi.License(name='MIT License'),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('media/', views.MediaItemListView.as_view(), name='media_list'),
    path('media/<pk>', views.MediaItemView.as_view(), name='media_item'),
    path('media/<pk>/upload', views.MediaItemUploadView.as_view(), name='media_upload'),
    path('media/<pk>/analytics', views.MediaAnalyticsView.as_view(), name='media_item_analytics'),
    path('channels/', views.ChannelListView.as_view(), name='channel_list'),
    path('channels/<pk>', views.ChannelView.as_view(), name='channel'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=None), name='schema-json'),
]
