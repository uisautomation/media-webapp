"""
Sitemap objects for use with the Django sitemap framework
(https://docs.djangoproject.com/en/2.1/ref/contrib/sitemaps/).

"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from mediaplatform import models as mpmodels


class MediaSitemap(Sitemap):
    """
    A sitemap object for all media items on the site.

    """
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        # We only show the most recently updated media items in the sitemap to avoid the sitemap
        # being an open DoS target
        return (
            mpmodels.MediaItem.objects.all().viewable_by_user(None)
            .order_by('-updated_at')[:200]
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('ui:media_item', kwargs={'pk': obj.id})


class StatcViewSitemap(Sitemap):
    """
    A sitemap object for the static views on the site.

    """
    changefreq = 'hourly'
    priority = 0.5

    def items(self):
        return ['home']

    def location(self, obj):
        return reverse(f'ui:{obj}')


# A sitemaps mapping for passing to the sitemaps framework in the top-level urlconf. Use like:
#
#     from api.sitemaps import sitemaps
#
#     path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
#          name='django.contrib.sitemaps.views.sitemap'),
sitemaps = {
    'media': MediaSitemap,
    'static': StatcViewSitemap,
}
