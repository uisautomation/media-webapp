"""
Django admin integration.

"""
from django import forms
from django.contrib import admin
from reversion.admin import VersionAdmin

from . import models


class RepositoryAdminForm(forms.ModelForm):
    class Meta:
        model = models.Repository
        fields = '__all__'
        widgets = {
            'basic_auth_password': forms.PasswordInput(),
        }


@admin.register(models.Repository)
class RepositoryAdmin(VersionAdmin):
    fields = ('url', 'basic_auth_user', 'basic_auth_password', 'last_harvested_at')
    form = RepositoryAdminForm
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('url',)


@admin.register(models.MetadataFormat)
class MetadataFormatAdmin(admin.ModelAdmin):
    fields = ('repository', 'identifier', 'namespace', 'schema', 'created_at', 'updated_at')
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('identifier', 'repository')


@admin.register(models.Record)
class RecordAdmin(admin.ModelAdmin):
    fields = ('identifier', 'datestamp', 'metadata_format', 'xml', 'harvested_at')
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('datestamp', 'identifier', 'metadata_format')
    ordering = ('-datestamp', 'identifier', 'metadata_format__identifier')
    search_fields = ('identifier',)

    # Since we use a deeply related object in the list, make sure we query it from the DB.
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('metadata_format')
