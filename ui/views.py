"""
Views

"""
import logging

from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.serializers import Serializer as NullSerializer

from api import views as apiviews
from . import serializers

LOG = logging.getLogger(__name__)


class ResourcePageMixin:
    """
    Mixin class for resource page views which simply renders the UI.

    """
    serializer_class = NullSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'index.html'


class MediaView(ResourcePageMixin, apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """
    A media item. Specialised to render a JSON-LD structured data representation of the media item
    as well.

    """
    serializer_class = serializers.MediaItemPageSerializer
    template_name = 'ui/media.html'


class ChannelView(ResourcePageMixin, apiviews.ChannelMixin, generics.RetrieveAPIView):
    """A channel."""


class PlaylistView(ResourcePageMixin, apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """A playlist"""
