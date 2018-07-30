import logging
from urllib import parse as urlparse

from django.conf import settings
from rest_framework import serializers

from smsjwplatform import jwplatform
from mediaplatform import models as mpmodels

LOG = logging.getLogger(__name__)


class SourceSerializer(serializers.Serializer):
    """
    A download source for a particular media type.

    """
    mime_type = serializers.CharField(source='type', help_text="The resource's MIME type")
    url = serializers.URLField(source='file', help_text="The resource's URL")
    width = serializers.IntegerField(help_text='The video width', required=False)
    height = serializers.IntegerField(help_text='The video height', required=False)


class LegacySMSMediaSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='Unique id for an SMS media')
    statisticsUrl = serializers.SerializerMethodField(help_text='Link to statistics page')

    def get_statisticsUrl(self, obj):
        return urlparse.urljoin(
            settings.LEGACY_SMS_FRONTEND_URL, f'media/{obj.id:d}/statistics')


class MediaSerializer(serializers.HyperlinkedModelSerializer):
    """
    An individual media item.

    This schema corresponds to Google's recommended layout for a Video object
    (https://developers.google.com/search/docs/data-types/video).

    """
    class Meta:
        model = mpmodels.MediaItem
        fields = (
            'id', 'name', 'description', 'duration', 'embedUrl', 'thumbnailUrl',
            'uploadDate', 'legacy', 'key'
        )

    # In JSON-LD, this should be "@id" but DRF doesn't make it easy to have @ signs in field naes
    # so we rename this field in to_representation() below.
    id = serializers.HyperlinkedIdentityField(
        view_name='api:media_item', help_text='Unique URL for the media')
    key = serializers.CharField(source='id', help_text='Unique id for media')
    name = serializers.CharField(source='title', help_text='Title of media')
    description = serializers.CharField(help_text='Description of media')
    duration = serializers.SerializerMethodField(
        help_text='Duration of the media in ISO 8601 format')
    embedUrl = serializers.SerializerMethodField(
        help_text='A URL to retrieve an embeddable player for the media item.'
    )
    thumbnailUrl = serializers.SerializerMethodField(
        help_text='A URL of a thumbnail/poster image for the media'
    )
    uploadDate = serializers.DateTimeField(source='published_at', help_text='Publication time')

    legacy = LegacySMSMediaSerializer(
        source='sms', help_text='Information from legacy SMS', required=False)

    def get_duration(self, obj):
        """Return the media item's duration in ISO 8601 format."""
        if obj.duration is None:
            return None

        hours, remainder = divmod(obj.duration, 3600)
        minutes, seconds = divmod(remainder, 60)

        return "PT{:d}H{:02d}M{:02.1f}S".format(int(hours), int(minutes), seconds)

    def get_media_id(self, obj):
        if not hasattr(obj, 'sms'):
            return None
        return obj.sms.id

    def get_embedUrl(self, obj):
        if not hasattr(obj, 'jwp'):
            return None
        return jwplatform.player_embed_url(
            obj.jwp.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'html',
            settings.JWPLATFORM_CONTENT_BASE_URL
        )

    def get_thumbnailUrl(self, obj):
        if not hasattr(obj, 'jwp'):
            return None
        return [
            jwplatform.Video({'key': obj.jwp.key}).get_poster_url(width=width)
            for width in [1280, 640, 320]
        ]

    def to_representation(self, obj):
        """
        Custom to_representation() override which adds JSON-LD fields.

        """
        data = super().to_representation(obj)
        data.update({
            '@id': data['id'],
            '@context': 'http://schema.org',
            '@type': 'VideoObject',
        })
        del data['id']
        return data


class MediaDetailSerializer(MediaSerializer):
    """
    Serialize a media object with greater detail for an individual media detail response

    """
    def get_sources(self, obj):
        if not obj.downloadable or not hasattr(obj, 'jwp'):
            return None

        video = jwplatform.DeliveryVideo.from_key(obj.jwp.key)

        return SourceSerializer(video.get('sources'), many=True).data

    def to_representation(self, obj):
        """
        Custom to_representation() subclass which examines the sources to set the "best" source
        in contentUrl.

        """
        data = super().to_representation(obj)
        sources = self.get_sources(obj)

        if sources is not None and len(sources) > 0:
            audio_sources = [s for s in sources if s.get('mime_type') == 'audio/mp4']
            video_sources = sorted(
                (
                    s for s in sources
                    if s.get('mime_type') == 'video/mp4' and s.get('height') is not None
                ),
                key=lambda s: s.get('height'), reverse=True)

            if len(video_sources) > 0:
                data['contentUrl'] = video_sources[0].get('url')
            elif len(audio_sources) > 0:
                data['contentUrl'] = audio_sources[0].get('url')

        return data


class CollectionSerializer(serializers.Serializer):
    """
    An individual collection.

    """
    id = serializers.CharField(source='key', help_text='Unique id for the collection')
    title = serializers.CharField(help_text='Title of collection')
    description = serializers.CharField(help_text='Description of collection')
    poster_image_url = serializers.SerializerMethodField(
        help_text='A URL of a thumbnail/poster image for the collection')
    collection_id = serializers.SerializerMethodField(help_text='Unique id for an SMS collection')

    def get_collection_id(self, obj):
        return obj.collection_id

    def get_poster_image_url(self, obj):
        return obj.get_poster_url()


class CollectionListSerializer(serializers.Serializer):
    """
    A collection list response.

    """
    results = CollectionSerializer(many=True, source='channels')
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    total = serializers.IntegerField()


class CollectionListQuerySerializer(serializers.Serializer):
    """
    A collection list query.

    """
    search = serializers.CharField(
        required=False,
        help_text='Free text search for collection'
    )


class ProfileSerializer(serializers.Serializer):
    """
    The profile of the current user.

    """
    is_anonymous = serializers.BooleanField(source='user.is_anonymous')
    username = serializers.CharField(source='user.username')
    urls = serializers.DictField()
