"""
Views

"""
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer

from api import views as apiviews, permissions
from . import serializers

LOG = logging.getLogger(__name__)


class MediaView(apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """View for rendering an individual media item. Extends the DRF's media item view."""
    serializer_class = serializers.MediaItemPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/media.html'


class MediaEditView(MediaView):
    """Identical to MediaView except it throws 403 if user doesn't have edit permission
    on the media item"""
    permission_classes = MediaView.permission_classes + [
        permissions.MediaPlatformEditPermission
    ]


class MediaItemAnalyticsView(apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """
    View for rendering an individual media item's analytics.
    Extends the DRF's media item analytics view.

    """
    serializer_class = serializers.MediaItemAnalyticsPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/analytics.html'


class ChannelView(apiviews.ChannelMixin, generics.RetrieveAPIView):
    """View for rendering an individual channel. Extends the DRF's channel view."""
    serializer_class = serializers.ChannelPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/resource.html'


class PlaylistView(apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """View for rendering an individual playlist. Extends the DRF's channel view."""
    serializer_class = serializers.PlaylistPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/resource.html'
