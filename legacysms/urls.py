"""
URL routing schema for Support for Legacy SMS.

"""

from django.urls import path

from . import views

app_name = "legacy-sms"

urlpatterns = [
    path('example', views.example, name='example'),
]
