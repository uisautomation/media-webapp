"""
Django admin integration.

"""
from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
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
        'title', 'description', 'series', 'updated_at', 'created_at'
    )
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('get_datestamp', 'get_identifier', 'get_title', 'series')
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


@admin.register(models.Series)
class SeriesAdmin(admin.ModelAdmin):
    fields = (
        'identifier', 'repository', 'title', 'track_types', 'playlist',
        'view_crsids', 'view_lookup_groups', 'view_lookup_insts',
        'view_is_public', 'view_is_signed_in', 'updated_at', 'created_at'
    )
    readonly_fields = ('updated_at', 'created_at')
    list_display = ('get_identifier', 'get_title', 'repository', 'updated_at', 'created_at')
    ordering = ('-updated_at', 'identifier')
    inlines = (MatterhornRecordInline,)
    autocomplete_fields = ('playlist', 'repository')
    search_fields = ('identifier', 'title')

    def get_identifier(self, obj):
        if obj.identifier == '':
            return 'Default series'
        return obj.identifier
    get_identifier.short_description = 'identifier'
    get_identifier.admin_order_field = 'identifier'

    def get_title(self, obj):
        if obj.title == '':
            return '\N{EM DASH}'
        return obj.title
    get_title.short_description = 'title'
    get_title.admin_order_field = 'title'


@admin.register(models.Track)
class TrackAdmin(admin.ModelAdmin):
    fields = (
        'identifier', 'matterhorn_record', 'url', 'media_item', 'xml', 'created_at', 'updated_at'
    )
    readonly_fields = ('updated_at', 'created_at')
    list_display = (
        'identifier', 'matterhorn_record', 'get_media_item', 'get_link', 'get_datestamp'
    )
    ordering = ('-matterhorn_record__record__datestamp', 'identifier')
    autocomplete_fields = ('matterhorn_record', 'media_item')

    # Since we use a deeply related object in the list, make sure we query it from the DB.
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('matterhorn_record__record')

    def get_media_item(self, obj):
        if not hasattr(obj, 'media_item') or obj.media_item is None:
            return '\N{EM DASH}'
        url = reverse('ui:media_item', kwargs={'pk': obj.media_item.id})
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.media_item.id)
    get_media_item.short_description = 'Media item'

    def get_link(self, obj):
        if obj.url == '':
            return '\N{EM DASH}'
        return format_html('<a href="{}" target="_blank">Link</a>', obj.url)
    get_link.short_description = 'link'

    def get_datestamp(self, obj):
        return obj.matterhorn_record.record.datestamp
    get_datestamp.short_description = 'Record datestamp'
    get_datestamp.ordering = 'matterhorn_record__record__datestamp'
