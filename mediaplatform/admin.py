import datetime

from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.formats import localize
from django.utils.html import format_html

from smsjwplatform import jwplatform as api
from mediaplatform_jwp import models as jwpmodels
from legacysms import models as smsmodels

from . import models


class PermissionInline(admin.StackedInline):
    model = models.Permission
    can_delete = False


class MediaItemViewPermissionInline(PermissionInline):
    fk_name = 'allows_view_item'
    verbose_name_plural = 'View Permissions'


class MediaItemEditPermissionInline(PermissionInline):
    fk_name = 'allows_edit_item'
    verbose_name_plural = 'Edit Permissions'


# TODO: it would be nice to refactor the mediaplatform admin to be unaware of the JWP/SMS models
# and use something like https://github.com/kux/django-admin-extend in the
# mediaplatform_jwp/legacysms applications instead.

class JWPVideoInline(admin.StackedInline):
    model = jwpmodels.Video
    fields = ('link', 'updated', 'updated_datetime')
    readonly_fields = ('link', 'updated', 'updated_datetime')
    can_delete = False
    verbose_name_plural = 'JWPlatform Videos'

    def player_html_url(self, obj):
        return api.player_embed_url(obj.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'html')

    def link(self, obj):
        if obj.key is None or obj.key == '':
            return '\N{EM DASH}'

        return format_html(
            '<a href="{}">{}</a> (<a href="{}" target="_blank">preview</a>)',
            reverse('admin:mediaplatform_jwp_video_change', args=(obj.key,)),
            obj.key,
            self.player_html_url(obj)
        )

    link.short_description = 'Video'

    def updated_datetime(self, obj):
        if obj.updated is None:
            return '\N{EM DASH}'
        return localize(datetime.datetime.fromtimestamp(obj.updated))

    updated_datetime.short_description = 'Last updated'


class SMSMediaItemInline(admin.StackedInline):
    model = smsmodels.MediaItem
    verbose_name_plural = 'SMS Media Items'
    readonly_fields = ('link', 'last_updated_at')

    def link(self, obj):
        return format_html(
            '<a href="{}">{}</a> (<a href="{}">legacy site</a>)',
            reverse('admin:legacysms_mediaitem_change', args=(obj.id,)),
            obj.id, 'https://sms.cam.ac.uk/media/{}'.format(obj.id),
        )

    link.short_description = 'Legacy SMS media item'


class UploadEndpointInline(admin.StackedInline):
    model = models.UploadEndpoint
    readonly_fields = ('url', 'expires_at')


class MediaItemAdminForm(forms.ModelForm):
    """
    A custom form for rendering a MediaItem in the admin which uses single-line input widgets for
    the title and copyright.

    """
    class Meta:
        fields = '__all__'
        model = models.MediaItem
        widgets = {
            'title': admin.widgets.AdminTextInputWidget,
            'copyright': admin.widgets.AdminTextInputWidget,
        }


@admin.register(models.MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    fields = (
        'preview', 'channel', 'type', 'title', 'description', 'formatted_duration',
        'published_at', 'downloadable', 'tags', 'language', 'copyright', 'created_at',
        'updated_at', 'deleted_at',
    )
    list_display = (
        'title', 'type', 'downloadable', 'published_at', 'deleted'
    )
    ordering = ('-published_at', 'title', 'id')
    search_fields = ('id', 'title', 'description', 'jwp__key')
    inlines = [
        UploadEndpointInline,
        SMSMediaItemInline,
        JWPVideoInline,
        MediaItemViewPermissionInline,
        MediaItemEditPermissionInline,
    ]
    readonly_fields = (
        'created_at', 'deleted', 'formatted_duration', 'preview', 'type',
        'updated_at'
    )
    form = MediaItemAdminForm

    def deleted(self, obj):
        """Whether the media item is marked as deleted."""
        return obj.deleted_at is not None

    deleted.boolean = True

    autocomplete_fields = ['channel']

    def formatted_duration(self, obj):
        """The duration of the video nicely formatted."""
        return localize(datetime.timedelta(seconds=obj.duration))

    formatted_duration.short_description = 'Duration'

    def player_html_url(self, obj):
        """
        Get a link to the HTML JWPlayer for the matching video or None if there is no matching JWP
        video.

        """
        if obj.jwp is None:
            return None
        return api.player_embed_url(obj.jwp.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'html')

    def preview(self, obj):
        """An IFrame containing a preview of the video."""
        url = self.player_html_url(obj)
        if url is None:
            return '\N{EM DASH}'

        return format_html(
            '<iframe width="640" height="360" src="{}"></iframe>', url
        )

    def get_search_results(self, request, queryset, search_term):
        """Allow searching by tag in addition to search_fields."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Also match on tags
        queryset |= self.model.objects.filter(tags__contains=[search_term.lower()])

        return queryset, use_distinct

    def get_queryset(self, request):
        """Ensure that related items are also fetched by the queryset."""
        return (
            models.MediaItem.objects_including_deleted
            .select_related('jwp')
            .select_related('sms')
            .select_related('view_permission')
            .select_related('edit_permission')
        )


class ChannelAdminForm(forms.ModelForm):
    """
    A custom form for rendering a Channel in the admin which uses a single-line input widget for
    the title.

    """
    class Meta:
        fields = '__all__'
        model = models.Channel
        widgets = {
            'title': admin.widgets.AdminTextInputWidget,
        }


class ChannelEditPermissionInline(PermissionInline):
    fk_name = 'allows_edit_channel'
    verbose_name_plural = 'Edit Permissions'


@admin.register(models.Channel)
class ChannelAdmin(admin.ModelAdmin):
    fields = ('title', 'description', 'item_count', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('id', 'title', 'description')
    list_display = ('title', 'deleted')
    ordering = ('title', 'id')
    inlines = [
        ChannelEditPermissionInline,
    ]
    readonly_fields = (
        'item_count', 'created_at', 'deleted', 'updated_at'
    )
    form = ChannelAdminForm

    def deleted(self, obj):
        """Whether the channel is marked as deleted."""
        return obj.deleted_at is not None

    deleted.boolean = True

    def item_count(self, obj):
        return obj.items.count()


class PlaylistAdminForm(forms.ModelForm):
    """
    A custom form for rendering a Playlist in the admin which uses a single-line input widget for
    the title.

    """
    class Meta:
        fields = '__all__'
        model = models.Playlist
        widgets = {
            'title': admin.widgets.AdminTextInputWidget,
        }


class PlaylistViewPermissionInline(PermissionInline):

    class InlineFormset(forms.models.BaseInlineFormSet):
        """
        Because the _playlist_post_save_handler creates a default Permission before this saves,
        we need to change the save_new() into a save_existing() to avoid a duplication error.
        TODO this doesn't seem to work because the default permission isn't overridden - however
        at least we don't get the error now.
        """
        def save_new(self, form, commit=True):
            playlist = form.cleaned_data['allows_view_playlist']
            instance = models.Permission.objects.get(allows_view_playlist=playlist)
            return self.save_existing(form, instance, commit=commit)

    fk_name = 'allows_view_playlist'
    verbose_name_plural = 'View Permissions'
    formset = InlineFormset


@admin.register(models.Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    fields = (
        'channel', 'title', 'description', 'media_items', 'created_at', 'updated_at', 'deleted_at'
    )
    search_fields = ('id', 'title', 'description')
    list_display = ('title', 'deleted')
    ordering = ('title', 'id')
    inlines = [
        PlaylistViewPermissionInline,
    ]
    readonly_fields = (
        'item_count', 'created_at', 'deleted', 'updated_at'
    )
    form = PlaylistAdminForm

    autocomplete_fields = ['channel']

    def deleted(self, obj):
        """Whether the channel is marked as deleted."""
        return obj.deleted_at is not None

    deleted.boolean = True

    def item_count(self, obj):
        return len(obj.media_items)
