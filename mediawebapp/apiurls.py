"""
API-related URLconf

"""
# DRF-YASG determines the basePath for an API by looking at the longest common prefix of *all* URLs
# in the urlconf. For pure API projects, this is fine but we also serve non-API views from
# different paths so we need to "trick" DRF-YASG into thinking the only URLs we serve are API
# related ones. Hence this module providing what would be the URLconf if this project were
# API-only. This trick means that DRF-YASG correctly sets the basePath of the swagger document to
# be "/api" and then separates all the resources out by the next component of the path.

from django.urls import path, re_path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

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
   urlconf='mediawebapp.apiurls',
)

urlpatterns = [
    path('api/', include('api.urls', namespace='api')),
    re_path(
        r'^api/swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=None), name='schema-json'),
]
