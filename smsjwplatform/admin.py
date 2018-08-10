from django.contrib import admin

from automationlookup.models import UserLookup
from smsjwplatform.models import CachedResource

admin.site.register(UserLookup, admin.ModelAdmin)


@admin.register(CachedResource)
class CachedResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'deleted_at')

    def get_queryset(self, request):
        # Since CachedResource has multiple managers, be explicit about which one should be used.
        return CachedResource.objects.all()

    def title(self, obj):
        return obj.data.get('title', '<no title>')
