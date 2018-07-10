from django.contrib import admin

from .models import MediaItem, Collection


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    pass
