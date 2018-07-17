from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import MediaItem, Collection


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    readonly_fields = ('preview', 'link', 'item_link', 'last_updated_at')

    def preview(self, obj):
        """An IFrame containing the legacy SMS embed."""
        return format_html(
            '<iframe width="640" height="360" src="{}"></iframe>',
            'https://sms.cam.ac.uk/media/{}/embed'.format(obj.id)
        )

    def link(self, obj):
        """A link back to the legacy SMS media item"""
        return format_html(
            '<a href="{url}">{url}</a>',
            url='https://sms.cam.ac.uk/media/{}'.format(obj.id)
        )

    def item_link(self, obj):
        """A link to the corresponding media item in the admin."""
        if obj.item is None:
            return '\N{EM DASH}'

        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:mediaplatform_mediaitem_change', args=(obj.item.pk,)),
            obj.item.title if obj.item.title != '' else '[Untitled]'
        )

    item_link.short_description = 'Media Item'


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    pass
