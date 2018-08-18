import logging
from urllib import parse as urlparse

from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import serializers

from mediaplatform import models as mpmodels
from mediaplatform_jwp.api import management as management

LOG = logging.getLogger(__name__)


# Model serializers for API calls
#
# The following serializers are to be used for list views and include minimal (if any) related
# resources.


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    """
    An individual channel.

    """
    class Meta:
        model = mpmodels.Channel
        fields = (
            'url', 'id', 'title', 'description', 'owningLookupInst', 'createdAt', 'updatedAt',
        )

        read_only_fields = (
            'url', 'id', 'createdAt', 'updatedAt',
        )
        extra_kwargs = {
            'createdAt': {'source': 'created_at'},
            'updatedAt': {'source': 'updated_at'},
            'owningLookupInst': {'source': 'owning_lookup_inst'},
            'url': {'view_name': 'api:channel'},
            'title': {'allow_blank': False},
        }

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
            obj = mpmodels.Channel.objects.create_for_user(request.user, **validated_data)
        else:
            obj = mpmodels.Channel.objects.create(**validated_data)

        return obj


class RelatedChannelIdField(serializers.PrimaryKeyRelatedField):
    """
    Related field serializer for media items or playlists which asserts that the channel field
    can only be set to a channel which the current user has edit permissions on. If there is no
    user, the empty queryset is returned.
    """
    def get_queryset(self):
        if self.context is None or 'request' not in self.context:
            return mpmodels.Channel.objects.none()

        user = self.context['request'].user

        return mpmodels.Channel.objects.all().editable_by_user(user)


class ChannelOwnedResourceModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Shared ModelSerializer between Media Items and Playlists as both are owned by a channel

    """

    channelId = RelatedChannelIdField(
        source='channel', required=True, help_text='Unique id of owning channel resource',
        write_only=True)

    def update(self, instance, validated_data):
        """
        Override behaviour when updating a media item or a playlist to stop the user changing
        the channel of an existing object.
        """
        # Note: channelId will already have been mapped into a channel object.
        if 'channel' in validated_data:
            raise serializers.ValidationError({
                'channelId': 'This field cannot be changed',
            })

        return super().update(instance, validated_data)


class PlaylistSerializer(ChannelOwnedResourceModelSerializer):
    """
    An individual playlist.

    """

    mediaUrl = serializers.SerializerMethodField(
        help_text='URL pointing to list of media items for this playlist', read_only=True
    )

    def get_mediaUrl(self, obj):
        # Get location of media list endpoint
        location = reverse('api:media_list')

        # Add query parameter
        location += '?' + urlencode({'playlist': obj.id})

        if self.context is None or 'request' not in self.context:
            return location

        return self.context['request'].build_absolute_uri(location)

    class Meta:
        model = mpmodels.Playlist
        fields = (
            'url', 'id', 'title', 'description', 'mediaIds', 'mediaUrl', 'channelId',
            'createdAt', 'updatedAt',
        )
        read_only_fields = (
            'url', 'id', 'mediaUrl', 'createdAt', 'updatedAt'
        )
        extra_kwargs = {
            'createdAt': {'source': 'created_at'},
            'updatedAt': {'source': 'updated_at'},
            'url': {'view_name': 'api:playlist'},
            'title': {'allow_blank': False},
            'mediaIds': {'source': 'media_items'}
        }


class MediaItemSerializer(ChannelOwnedResourceModelSerializer):
    """
    An individual media item.

    """

    class Meta:
        model = mpmodels.MediaItem
        fields = (
            'url', 'id', 'title', 'description', 'duration', 'type', 'publishedAt',
            'downloadable', 'language', 'copyright', 'tags', 'createdAt',
            'updatedAt', 'posterImageUrl', 'channelId', 'embedUrl', 'downloadableByUser',
        )

        read_only_fields = (
            'url', 'id', 'duration', 'type', 'createdAt', 'updatedAt',
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

    embedUrl = serializers.SerializerMethodField(
        help_text='A URL suitable for embedding this media item in an IFrame', read_only=True)

    downloadableByUser = serializers.BooleanField(
        source='downloadable_by_user',
        help_text=(
            'Whether the current user can download this media item. '
            'Some users can download media even if the downloadable flag is False.'
        ),
        read_only=True
    )

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
        return self._build_absolute_uri(reverse(
            'api:media_poster',
            kwargs={'pk': obj.id, 'width': 720, 'extension': 'jpg'}
        ))

    def get_embedUrl(self, obj):
        return self._build_absolute_uri(
            reverse('api:media_embed', kwargs={'pk': obj.id}))

    def _build_absolute_uri(self, uri):
        if 'request' in self.context:
            return self.context['request'].build_absolute_uri(uri)
        return uri


# Detail serialisers
#
# The following serialiser are to be used in individual resource views and include more information
# on related resources.


class ProfileSerializer(serializers.Serializer):
    """
    The profile of the current user.

    """
    isAnonymous = serializers.BooleanField(source='user.is_anonymous')
    username = serializers.CharField(source='user.username', required=False)
    channels = serializers.SerializerMethodField(
        help_text="List of channels which the user has edit rights on")
    displayName = serializers.CharField(source='person.displayName', required=False)
    avatarImageUrl = serializers.SerializerMethodField()

    def get_channels(self, obj):
        qs = mpmodels.Channel.objects.all().editable_by_user(obj['user'])
        return ChannelSerializer(qs, many=True, context=self.context).data

    def get_avatarImageUrl(self, obj):
        person = obj.get('person')
        if person is None:
            return None

        for attr in person.get('attributes', []):
            if attr.get('scheme') == 'jpegPhoto':
                return 'data:image/jpeg;base64,' + attr['binaryData']

        return None


class SourceSerializer(serializers.Serializer):
    """
    A download source for a particular media type.

    """
    mimeType = serializers.CharField(source='mime_type', help_text="The resource's MIME type")
    url = serializers.SerializerMethodField(help_text="The resource's URL")
    width = serializers.IntegerField(help_text='The video width', required=False)
    height = serializers.IntegerField(help_text='The video height', required=False)

    def get_url(self, source):
        query = QueryDict(mutable=True)
        query['mimeType'] = source.mime_type
        if source.width is not None:
            query['width'] = f'{source.width}'
        if source.height is not None:
            query['height'] = f'{source.height}'
        url = reverse('api:media_source', kwargs={'pk': source.item.id}) + '?' + query.urlencode()
        if 'request' in self.context:
            url = self.context['request'].build_absolute_uri(url)
        return url


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


class MediaItemDetailSerializer(MediaItemSerializer):
    """
    An individual media item including related resources.

    """
    class Meta(MediaItemSerializer.Meta):
        fields = MediaItemSerializer.Meta.fields + (
            'channel', 'sources', 'legacyStatisticsUrl', 'bestSourceUrl')

        read_only_fields = MediaItemSerializer.Meta.read_only_fields + ('sources',)

    channel = ChannelSerializer(read_only=True)

    sources = serializers.SerializerMethodField()

    legacyStatisticsUrl = serializers.SerializerMethodField()

    bestSourceUrl = serializers.SerializerMethodField()

    def get_legacyStatisticsUrl(self, obj):
        if not hasattr(obj, 'sms'):
            return None
        return urlparse.urljoin(
            settings.LEGACY_SMS_FRONTEND_URL, f'media/{obj.sms.id:d}/statistics')

    def get_bestSourceUrl(self, obj):
        if not obj.downloadable_by_user or len(obj.sources) == 0:
            return None
        url = reverse('api:media_source', kwargs={'pk': obj.id})
        if 'request' in self.context:
            url = self.context['request'].build_absolute_uri(url)
        return url

    def get_sources(self, obj):
        sources = obj.sources if obj.downloadable_by_user else []
        return SourceSerializer(sources, many=True, context=self.context).data


class MediaItemAnalyticsSerializer(serializers.Serializer):
    """
    The number of viewing for a particular media item on a particular day.

    """
    date = serializers.DateField(
        source='day', help_text='The day when a media was viewed', read_only=True)
    views = serializers.IntegerField(
        source='num_hits', help_text='The number of media views on a day', read_only=True)


class MediaItemAnalyticsListSerializer(serializers.Serializer):
    """
    A list of media analytics data points.

    """
    views_per_day = MediaItemAnalyticsSerializer(source='fetched_analytics', many=True)

    size = serializers.IntegerField(source='fetched_size')


class ChannelDetailSerializer(ChannelSerializer):
    """
    An individual channel including related resources.

    """
    class Meta(ChannelSerializer.Meta):
        fields = ChannelSerializer.Meta.fields + ('mediaUrl',)

    mediaUrl = serializers.SerializerMethodField(
        help_text='URL pointing to list of media items for this channel'
    )

    def get_mediaUrl(self, obj):
        # Get location of media list endpoint
        location = reverse('api:media_list')

        # Add query parameter
        location += '?' + urlencode({'channel': obj.id})

        if self.context is None or 'request' not in self.context:
            return location

        return self.context['request'].build_absolute_uri(location)


class PlaylistDetailSerializer(PlaylistSerializer):
    """
    An individual playlist including any information which should only appear in the detail view.

    """

    channel = ChannelSerializer(read_only=True)

    media = MediaItemSerializer(many=True, source='fetched_media_items_in_order')

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ('channel', 'media')
