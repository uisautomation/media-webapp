"""
Views

"""
import logging

from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer

from api import views as apiviews
from . import serializers

LOG = logging.getLogger(__name__)


class ResourcePageMixin(apiviews.ViewMixinBase):
    """
    Mixin class for views which ensured the returned object is decorated with the current user's
    profile as required by :py:class:`ui.serializers.ResourcePageSerializer`.

    """
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/resource.html'

    def get_object(self):
        obj = super().get_object()
        obj.profile = self.get_profile()
        return obj


class MediaView(ResourcePageMixin, apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """View for rendering an individual media item. Extends the DRF's media item view."""
    serializer_class = serializers.MediaItemPageSerializer
    template_name = 'ui/media.html'


class MediaItemAnalyticsView(ResourcePageMixin, apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """
    View for rendering an individual media item's analytics.
    Extends the DRF's media item analytics view.

    """
    serializer_class = serializers.ResourcePageSerializer


class ChannelView(ResourcePageMixin, apiviews.ChannelMixin, generics.RetrieveAPIView):
    """View for rendering an individual channel. Extends the DRF's channel view."""
    serializer_class = serializers.ChannelPageSerializer


class PlaylistView(ResourcePageMixin, apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """View for rendering an individual playlist. Extends the DRF's channel view."""
    serializer_class = serializers.PlaylistPageSerializer
