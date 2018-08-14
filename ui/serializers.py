import logging

from rest_framework import serializers

from api import serializers as apiserializers
from smsjwplatform import jwplatform

LOG = logging.getLogger(__name__)


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


class ResourcePageSerializer(serializers.Serializer):
    """
    Generic serializer for a page representing a resource. Adds the current user's profile to the
    context under the "profile" key.

    """
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        return apiserializers.ProfileSerializer(
            self.context['request'].user, context=self.context).data


class MediaItemPageSerializer(ResourcePageSerializer):
    """
    A serializer for media items which renders a ``json_ld`` field which is the representation
    of the media item in JSON LD format along with the resource.

    """
    json_ld = MediaItemJSONLDSerializer(source='*')
    resource = apiserializers.MediaItemDetailSerializer(source='*')


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
