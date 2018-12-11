"""
Views

"""
import logging

from django.http import Http404
from django.views.generic.base import RedirectView
from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.serializers import Serializer as NullSerializer

from api import views as apiviews
from mediaplatform_jwp.api import delivery

from . import renderers
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


class MediaItemRSSView(apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """
    Retrieve an individual media item as RSS.

    IMPORTANT: we do not want this sort of feed to proliferate and so it is only available for
    media items which were imported from the old SMS.

    """
    # We cannot simply make use of the normal DRF content negotiation and format_suffix_patterns()
    # because this results in an additional "format" parameter being passed to the class which is
    # then used to reverse() URLs for hyperlinked resources such as channels. Since none of those
    # views support the format parameter, the reverse() call used by HyperlinkedIdentityField
    # fails.
    renderer_classes = [renderers.RSSRenderer]
    serializer_class = serializers.MediaItemRSSSerializer

    def get_queryset(self):
        return super().get_queryset().filter(downloadable_by_user=True, sms__isnull=False)

    def get_object(self):
        obj = super().get_object()
        # We need to render a list of entries with just this media item as a single entry. This is
        # a bit of a hacky way of doing this but it works.
        obj.self_list = [obj]
        return obj


class MediaItemJWPlayerConfigurationView(apiviews.MediaItemMixin, generics.RetrieveAPIView):
    """
    Endpoint to retrieve JWP configuration for a media item.

    """
    serializer_class = serializers.JWPlayerConfigurationSerializer

    def get_object(self):
        # get_object will 404 if the object does not exist
        item = super().get_object()

        # if there is no equivalent JWP video, 404
        if not hasattr(item, 'jwp'):
            raise Http404()

        # Annotate item with a list containing itself. This somewhat odd construction is required
        # to allow the same schema for playlists as well as individual media items.
        item.items_for_user = [item]

        return item


class ChannelView(ResourcePageMixin, apiviews.ChannelMixin, generics.RetrieveAPIView):
    """A channel."""


class PlaylistView(ResourcePageMixin, apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """A playlist"""


class PlaylistRSSView(apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """
    Retrieve an individual playlist as RSS.

    """
    # We cannot simply make use of the normal DRF content negotiation and format_suffix_patterns()
    # because this results in an additional "format" parameter being passed to the class which is
    # then used to reverse() URLs for hyperlinked resources such as channels. Since none of those
    # views support the format parameter, the reverse() call used by HyperlinkedIdentityField
    # fails.
    renderer_classes = [renderers.RSSRenderer]
    serializer_class = serializers.PlaylistRSSSerializer

    def get_object(self):
        obj = super().get_object()
        obj.downloadable_media_items = (
            self.filter_media_item_qs(obj.ordered_media_item_queryset)
            .downloadable_by_user(self.request.user)
        )
        return obj


class PlaylistJWPlayerConfigurationView(apiviews.PlaylistMixin, generics.RetrieveAPIView):
    """
    Endpoint to retrieve JWP configuration for a playlist.

    """
    serializer_class = serializers.JWPlayerConfigurationSerializer

    def get_object(self):
        # get_object will 404 if the object does not exist
        playlist = super().get_object()

        # Get the media items which the user can view and which have a JWP video.
        items = (
            playlist.ordered_media_item_queryset
            .filter(jwp__isnull=False)
            .viewable_by_user(self.request.user)
        )

        # Annotate the playlist with the items.
        playlist.items_for_user = items

        return playlist


class PlayerLibraryView(RedirectView):
    """
    Redirect to configured JWPlayer library.

    """
    def get_redirect_url(self, *args, **kwargs):
        # The JWP player URL is signed and so, annoyingly, must be re-generated each time.
        return delivery.player_library_url()
