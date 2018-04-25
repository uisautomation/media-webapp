from django.contrib import admin

# Register your models here.
from django.contrib.admin import ModelAdmin

from oauthcommon.models import UserLookup

admin.site.register(UserLookup, ModelAdmin)
