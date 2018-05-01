from django.contrib import admin

# Register your models here.
from django.contrib.admin import ModelAdmin

from automationlookup.models import UserLookup

admin.site.register(UserLookup, ModelAdmin)
