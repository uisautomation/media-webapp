import logging

from django.urls import reverse
from rest_framework import serializers

from api import serializers as apiserializers
from mediaplatform_jwp.api import delivery as jwplatform

LOG = logging.getLogger(__name__)

MIME_TYPE_MAPPING = {'video': 'video/mp4', 'audio': 'audio/mp4'}


# Model serializers for views

class JSONLDMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, clsname, bases, attrs):
        for field_name in ['id']:
            if field_name in attrs:
                attrs['@' + field_name] = attrs[field_name]
                del attrs[field_name]
        return super().__new__(cls, clsname, bases, attrs)


class JSONLDSerializer(serializers.Serializer, metaclass=JSONLDMetaclass):
    def to_representation(self, value):
        data = super().to_representation(value)

        context = getattr(self, 'jsonld_context')
        if context is not None:
            data['@context'] = context

        type_ = getattr(self, 'jsonld_type')
        if type_ is not None:
            data['@type'] = type_

        return data


class MediaItemJSONLDSerializer(JSONLDSerializer):
    """
    Serialise media items as a JSON-LD VideoObject (https://schema.org/VideoObject) taking into
    account Google's recommended fields:
    https://developers.google.com/search/docs/data-types/video.

    """
    jsonld_context = 'http://schema.org'
    jsonld_type = 'VideoObject'

    id = serializers.HyperlinkedIdentityField(
        view_name='api:media_item', help_text='Unique URL for the media', read_only=True)

    name = serializers.CharField(source='title', help_text='Title of media')

    description = serializers.CharField(
        help_text='Description of media', required=False, allow_blank=True)

    duration = serializers.SerializerMethodField(
        help_text='Duration of the media in ISO 8601 format', read_only=True)

    thumbnailUrl = serializers.SerializerMethodField(
        help_text='A URL of a thumbnail/poster image for the media', read_only=True)

    uploadDate = serializers.DateTimeField(
        source='published_at', help_text='Publication time', read_only=True)

    embedUrl = serializers.SerializerMethodField()

    contentUrl = serializers.SerializerMethodField()

    def get_duration(self, obj):
        """Return the media item's duration in ISO 8601 format."""
        if obj.duration is None:
            return None

        hours, remainder = divmod(obj.duration, 3600)
        minutes, seconds = divmod(remainder, 60)

        return "PT{:d}H{:02d}M{:02.1f}S".format(int(hours), int(minutes), seconds)

    def get_thumbnailUrl(self, obj):
        if not hasattr(obj, 'jwp'):
            return None
        return [
            jwplatform.Video({'key': obj.jwp.key}).get_poster_url(width=width)
            for width in [1920, 1280, 640, 320]
        ]

    def get_embedUrl(self, obj):
        return self._reverse('api:media_embed', kwargs={'pk': obj.id})

    def get_contentUrl(self, obj):
        if not obj.downloadable_by_user:
            return None
        return self._reverse('api:media_source', kwargs={'pk': obj.id})

    def _reverse(self, *args, **kwargs):
        """
        Wrapper around Django's reverse() utility function which attempts to use the request in
        the serialiser context (if any) to build an absolute URI.

        """
        uri = reverse(*args, **kwargs)
        if 'request' not in self.context:
            return uri
        return self.context['request'].build_absolute_uri(uri)


class ResourcePageSerializer(serializers.Serializer):
    """
    Generic serializer for a page representing a resource. Adds the current user's profile to the
    context under the "profile" key.

    """
    profile = apiserializers.ProfileSerializer(read_only=True)


class MediaItemPageSerializer(ResourcePageSerializer):
    """
    A serializer for media items which renders a ``json_ld`` field which is the representation of
    the media item in JSON LD format along with the resource.

    """
    json_ld = MediaItemJSONLDSerializer(source='*')

    resource = apiserializers.MediaItemDetailSerializer(source='*')


class MediaItemRSSEntitySerializer(serializers.Serializer):
    """

    """
    url = serializers.HyperlinkedIdentityField(view_name='ui:media_item')
    imageUrl = serializers.SerializerMethodField()
    title = serializers.CharField()
    description = serializers.CharField()
    duration = serializers.IntegerField()
    rights = serializers.CharField(source='copyright')
    published_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    enclosures = serializers.SerializerMethodField()

    def get_imageUrl(self, obj):
        return self._absolute_uri(reverse('api:media_poster', kwargs={
            'pk': obj.id, 'width': 1920, 'extension': 'jpg'
        }))

    def get_enclosures(self, obj):
        # Really we should simply use the sources attribute on the media item and serialise this
        # with something like a MediaItemSourceRSSEnclosureSerializer. Unfortunately, getting the
        # "sources" attribute requires a call to the JWP delivery API and may be too expensive/slow
        # if there are large numbers of media items. In the future, if sources are cached in the
        # database, we can do this "properly".
        return [{
            'url': self._absolute_uri(reverse('api:media_source', kwargs={'pk': obj.id})),
            'mime_type': MIME_TYPE_MAPPING.get(obj.type, 'application/octet-stream')
        }]

    def _absolute_uri(self, uri):
        request = self.context.get('request')
        if request is None:
            return uri
        return request.build_absolute_uri(uri)


class MediaItemRSSSerializer(serializers.Serializer):
    """
    Serialise a media item resource into data suitable for :py:class:`ui.renderers.RSSRenderer`.

    """
    url = serializers.HyperlinkedIdentityField(view_name='ui:media_item_rss')
    title = serializers.CharField()
    description = serializers.CharField()
    entries = MediaItemRSSEntitySerializer(many=True, source='self_list')


class ChannelPageSerializer(ResourcePageSerializer):
    """
    A serializer for channels which renders the API resource.

    """
    resource = apiserializers.ChannelDetailSerializer(source='*')


class PlaylistPageSerializer(ResourcePageSerializer):
    """
    A serializer for playlists which renders the API resource.

    """
    resource = apiserializers.PlaylistDetailSerializer(source='*')


class MediaItemAnalyticsPageSerializer(ResourcePageSerializer):
    """
    A serializer for media items which renders the media item resource and analytics into the view.

    """
    resource = apiserializers.MediaItemDetailSerializer(source='*')
    analytics = apiserializers.MediaItemAnalyticsListSerializer(source='*')


class PlaylistRSSSerializer(serializers.Serializer):
    """
    Serialise a playlist resource into data suitable for :py:class:`ui.renderers.RSSRenderer`.

    """
    url = serializers.HyperlinkedIdentityField(view_name='ui:playlist_rss')
    title = serializers.CharField()
    description = serializers.CharField()
    entries = MediaItemRSSEntitySerializer(many=True, source='downloadable_media_items')
