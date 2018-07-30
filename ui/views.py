"""
Views

"""
import json
import logging

from rest_framework.renderers import TemplateHTMLRenderer

import api

LOG = logging.getLogger(__name__)


class MediaView(api.views.MediaView):
    """View for rendering an individual media item. Extends the DRF's media item view."""

    renderer_classes = [TemplateHTMLRenderer]

    template_name = 'ui/media.html'

    def get(self, request, pk):
        response = super().get(request, pk)
        response.data['media_item_json'] = json.dumps(response.data)
        return response
