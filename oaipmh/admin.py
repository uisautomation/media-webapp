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


@admin.register(models.MatterhornRecord)
class MatterhornRecordAdmin(admin.ModelAdmin):
    fields = (
        'title', 'description', 'updated_at', 'created_at'
    )
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('get_datestamp', 'get_identifier', 'get_title')
    ordering = ('-record__datestamp', 'title',)
    search_fields = ('record__identifier', 'title', 'description')

    # Since we use a deeply related object in the list, make sure we query it from the DB.
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('record')

    def get_title(self, obj):
        if obj.title == '':
            return '\N{EM DASH}'
        return obj.title
    get_title.short_description = 'title'
    get_title.admin_order_field = 'title'

    def get_datestamp(self, obj):
        return obj.record.datestamp
    get_datestamp.short_description = 'datestamp'
    get_datestamp.admin_order_field = 'record__datestamp'

    def get_identifier(self, obj):
        return obj.record.identifier
    get_identifier.short_description = 'identifier'
    get_identifier.admin_order_field = 'record__identifier'


class MatterhornRecordInline(admin.TabularInline):
    model = models.MatterhornRecord
    can_delete = False
    verbose_name_plural = "Records"


@admin.register(models.Record)
class RecordAdmin(admin.ModelAdmin):
    fields = ('identifier', 'datestamp', 'metadata_format', 'xml', 'harvested_at')
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('datestamp', 'identifier', 'metadata_format')
    ordering = ('-datestamp', 'identifier', 'metadata_format__identifier')
    search_fields = ('identifier',)
    inlines = (MatterhornRecordInline,)

    # Since we use a deeply related object in the list, make sure we query it from the DB.
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('metadata_format')
