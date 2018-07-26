import datetime

from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.formats import localize
from django.utils.html import format_html

from smsjwplatform import jwplatform as api

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    fields = ('key', 'preview', 'item_link', 'updated_datetime', 'updated')
    list_display = ('key', 'item_link', 'updated_datetime')
    search_fields = ('key', 'item__title', 'item__description')
    readonly_fields = ('key', 'updated', 'updated_datetime', 'item_link', 'preview')

    def updated_datetime(self, obj):
        """A more friendly "updated" time which presents it as a localised string."""
        return localize(datetime.datetime.fromtimestamp(obj.updated))

    updated_datetime.short_description = 'Last updated'

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

    def preview(self, obj):
        """An IFrame containing the JWPlatform hosted video."""
        url = api.player_embed_url(obj.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'html')
        return format_html(
            '<iframe width="640" height="360" src="{}"></iframe>', url
        )

    def get_search_results(self, request, queryset, search_term):
        """Allow searching by item tag in addition to the fields in search_fields."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Also match on item tags
        queryset |= self.model.objects.filter(item__tags__contains=[search_term.lower()])

        return queryset, use_distinct

    def get_queryset(self, request):
        """Ensure that related items are also fetched by the queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('item')
