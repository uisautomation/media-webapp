"""smswebapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

import automationcommon.views

# Django debug toolbar is only installed in developer builds
try:
    import debug_toolbar.urls
    HAVE_DDT = True
except ImportError:
    HAVE_DDT = False

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ucamwebauth.urls')),
    path('status', automationcommon.views.status, name='status'),
    path('legacy/', include('smsjwplatform.urls')),
    path('legacy/', include('legacysms.urls', namespace='legacysms')),
]

# Selectively enable django debug toolbar URLs. Only if the toolbar is
# installed *and* DEBUG is True.
if HAVE_DDT and settings.DEBUG:
    urlpatterns = [
        path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
