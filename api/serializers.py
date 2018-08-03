import logging
from urllib import parse as urlparse

from django.conf import settings
from rest_framework import serializers

from smsjwplatform import jwplatform
from mediaplatform import models as mpmodels
from mediaplatform_jwp import management

LOG = logging.getLogger(__name__)


class SourceSerializer(serializers.Serializer):
    """
    A download source for a particular media type.

    """
    mimeType = serializers.CharField(source='type', help_text="The resource's MIME type")
    url = serializers.URLField(source='file', help_text="The resource's URL")
    width = serializers.IntegerField(help_text='The video width', required=False)
    height = serializers.IntegerField(help_text='The video height', required=False)


class LegacySMSMediaSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='Unique id for an SMS media')
    statisticsUrl = serializers.SerializerMethodField(help_text='Link to statistics page')

    def get_statisticsUrl(self, obj):
        return urlparse.urljoin(
            settings.LEGACY_SMS_FRONTEND_URL, f'media/{obj.id:d}/statistics')


class MediaItemSerializer(serializers.HyperlinkedModelSerializer):
    """
    An individual media item.

    This schema corresponds to Google's recommended layout for a Video object
    (https://developers.google.com/search/docs/data-types/video).

    """
    class Meta:
        model = mpmodels.MediaItem
        fields = (
            'url', 'id', 'title', 'description', 'duration', 'type', 'publishedAt',
            'downloadable', 'language', 'copyright', 'tags', 'createdAt',
            'updatedAt', 'posterImageUrl',
        )

        read_only_fields = (
            'url', 'id', 'duration', 'type', 'created_at', 'updated_at', 'posterImageUrl'
        )
        extra_kwargs = {
            'createdAt': {'source': 'created_at'},
            'publishedAt': {'source': 'published_at'},
            'updatedAt': {'source': 'updated_at'},
            'url': {'view_name': 'api:media_item'},
            'title': {'allow_blank': False},
        }

    posterImageUrl = serializers.SerializerMethodField(
        help_text='A URL of a thumbnail/poster image for the media', read_only=True)

    def create(self, validated_data):
        """
        Override behaviour when creating a new object using this serializer. If the current request
        is being passed in the context, give the request user edit and view permissions on the
        item.

        """
        request = None
        if self.context is not None and 'request' in self.context:
            request = self.context['request']

        if request is not None and not request.user.is_anonymous:
            obj = mpmodels.MediaItem.objects.create_for_user(request.user, **validated_data)
        else:
            obj = mpmodels.MediaItem.objects.create(**validated_data)

        return obj

    def get_posterImageUrl(self, obj):
        if not hasattr(obj, 'jwp'):
            return None
        return jwplatform.Video({'key': obj.jwp.key}).get_poster_url(width=640)


class MediaItemLinksSerializer(serializers.Serializer):
    legacyStatisticsUrl = serializers.SerializerMethodField()
    embedUrl = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField(source='*')

    def get_legacyStatisticsUrl(self, obj):
        if not hasattr(obj, 'sms'):
            return None
        return urlparse.urljoin(
            settings.LEGACY_SMS_FRONTEND_URL, f'media/{obj.sms.id:d}/statistics')

    def get_embedUrl(self, obj):
        if not hasattr(obj, 'jwp'):
            return None
        return jwplatform.player_embed_url(
            obj.jwp.key, settings.JWPLATFORM_EMBED_PLAYER_KEY, 'html',
            settings.JWPLATFORM_CONTENT_BASE_URL
        )

    def get_sources(self, obj):
        if not obj.downloadable or not hasattr(obj, 'jwp'):
            return None

        video = jwplatform.DeliveryVideo.from_key(obj.jwp.key)

        return SourceSerializer(video.get('sources'), many=True).data


class MediaItemDetailSerializer(MediaItemSerializer):
    """
    Serialize a media object with greater detail for an individual media detail response

    """
    class Meta(MediaItemSerializer.Meta):
        fields = MediaItemSerializer.Meta.fields + ('links',)

    links = MediaItemLinksSerializer(source='*', read_only=True)


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


class MediaUploadSerializer(serializers.Serializer):
    """
    A serializer which returns an upload endpoint for a media item. Intended to be used as custom
    serializer in an UpdateView for MediaItem models.

    """
    url = serializers.URLField(source='upload_endpoint.url', read_only=True)
    expires_at = serializers.DateTimeField(source='upload_endpoint.expires_at', read_only=True)

    def update(self, instance, verified_data):
        # TODO: abstract the creation of UploadEndpoint objects to be backend neutral
        management.create_upload_endpoint(instance)
        return instance


class MediaAnalyticsItemSerializer(serializers.Serializer):
    """
    The number of viewing for a particular media item on a particular day.

    """
    date = serializers.SerializerMethodField(help_text='The day when a media was viewed')
    views = serializers.SerializerMethodField(help_text='The number of media views on a day')

    def get_date(self, row):
        return str(row[0])

    def get_views(self, row):
        return row[1]


class MediaAnalyticsListSerializer(serializers.Serializer):
    """
    A list of media analytics data points.

    """
    results = MediaAnalyticsItemSerializer(many=True, source='*')
