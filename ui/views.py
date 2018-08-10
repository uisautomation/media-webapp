"""
Views

"""
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer

from api import views as apiviews
from . import serializers

LOG = logging.getLogger(__name__)


# The UI views are not part of the API and should not appear in the swagger docs
@method_decorator(name='get', decorator=swagger_auto_schema(auto_schema=None))
class MediaView(apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """View for rendering an individual media item. Extends the DRF's media item view."""
    serializer_class = serializers.MediaItemPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/media.html'


@login_required
def upload(request):
    return render(request, 'ui/upload.html')


class MediaAnalyticsView(apiviews.MediaAnalyticsView):
    """
    View for rendering an individual media item's analytics.
    Extends the DRF's media item analytics view.

    """
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/analytics.html'


# The UI views are not part of the API and should not appear in the swagger docs
@method_decorator(name='get', decorator=swagger_auto_schema(auto_schema=None))
class ChannelView(apiviews.ChannelMixin, generics.RetrieveAPIView):
    """View for rendering an individual channel. Extends the DRF's channel view."""
    serializer_class = serializers.ChannelPageSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'ui/resource.html'
