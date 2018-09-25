"""
Views implementing the API endpoints.

"""
import logging

import automationlookup
from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import redirect, render
from django_filters import rest_framework as df_filters
from drf_yasg import inspectors, openapi
from rest_framework import generics, pagination, filters, views
from rest_framework.exceptions import ParseError
import requests

import mediaplatform.models as mpmodels

from . import permissions
from . import serializers


LOG = logging.getLogger(__name__)


def annotate_channel_qs_for_detail(qs, user=None, name='item_count'):
    """
    Annotate a queryset returning Channel objects so that they can be serialised by a
    ChannelDetailSerializer.

    """
    items_qs = (
        mpmodels.MediaItem.objects.all().viewable_by_user(user)
        .filter(channel=models.OuterRef('pk'))
        .values('channel')
        .annotate(count=models.Count('*'))
        .values('count')
    )
    return qs.annotate(**{name: models.Subquery(items_qs, output_field=models.BigIntegerField())})


def get_profile(request):
    """
    Return an object representing what is known about a user from a reques. Contains two keys:
    ``user`` which is simply the user object from the request and ``person`` which is the lookup
    person resource for the user is non-anoymous.

    """
    obj = {
        'user': request.user,
        'channels': annotate_channel_qs_for_detail(
            mpmodels.Channel.objects.all().editable_by_user(request.user),
            user=request.user
        ),
    }
    if not request.user.is_anonymous:
        try:
            obj['person'] = automationlookup.get_person(
                identifier=request.user.username,
                scheme=getattr(settings, 'LOOKUP_SCHEME', 'crsid'),
                fetch=['jpegPhoto'],
            )
        except requests.HTTPError as e:
            LOG.warning('Error fetching person: %s', e)
    return obj


class ProfileView(generics.RetrieveAPIView):
    """
    Endpoint to retrieve the profile of the current user.

    """
    serializer_class = serializers.ProfileSerializer

    def get_object(self):
        return get_profile(self.request)


class ListPagination(pagination.CursorPagination):
    page_size = 50


class ListMixinBase:
    """
    Base class for the various ListView mixin classes which ensures that the list only contains
    resources viewable by the user, annotates the resources with the viewable and editable
    flags and selects related JWPlatform and SMS objects.

    Sets permission_classes to :py:class:`~.permissions.MediaPlatformPermission` so that safe and
    unsafe operations are appropriately restricted.

    """
    permission_classes = [permissions.MediaPlatformPermission]

    def get_queryset(self):
        return (
            super().get_queryset().all()
            .viewable_by_user(self.request.user)
            .annotate_viewable(self.request.user)
            .annotate_editable(self.request.user)
            .select_related('sms')
        )


class MediaItemListSearchFilter(filters.SearchFilter):
    """
    Custom filter based on :py:class:`rest_framework.filters.SearchFilter` specialised to search
    :py:class:`mediaplatform.models.MediaItem` objects. If the "tags" field is specified in the
    view's ``search_fields`` attribute, then the tags field is searched for any tag matching the
    lower cased search term.

    """

    def get_search_term(self, request):
        return request.query_params.get(self.search_param, '')

    def get_search_terms(self, request):
        return [self.get_search_term(request)]

    def filter_queryset(self, request, queryset, view):
        filtered_qs = super().filter_queryset(request, queryset, view)

        if 'tags' in getattr(view, 'search_fields', ()):
            search_term = self.get_search_term(request)
            filtered_qs |= queryset.filter(tags__contains=[search_term.lower()])

        return filtered_qs


class MediaItemListMixin(ListMixinBase):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for listing
    (and possibly creating/deleting) media items. Use this mixin with ListAPIView or
    ListCreateAPIView to form a concrete view class.

    """
    queryset = mpmodels.MediaItem.objects

    def get_queryset(self):
        return (
            super().get_queryset().all()
            .annotate_downloadable(self.request.user)
            .select_related('jwp')
        )


class MediaItemMixin(MediaItemListMixin):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for
    retrieving (and possibly updating) individual media items. Use this mixin with RetrieveAPIView
    or RetrieveUpdateAPIView to form a concrete view class.

    """


def _user_playlists(request):
    """
    Return a queryset from a request which contains all the playlists which are viewable by the
    user making the request.

    """
    user = request.user if request is not None else None
    return mpmodels.Playlist.objects.all().viewable_by_user(user)


class MediaItemFilter(df_filters.FilterSet):
    class Meta:
        model = mpmodels.MediaItem
        fields = ('channel', 'playlist')

    playlist = df_filters.ModelChoiceFilter(
        label='Playlist', method='filter_playlist',
        help_text='Only media items from this playlist will be listed',
        queryset=_user_playlists)

    def filter_playlist(self, queryset, name, value):
        """
        Filter media items to only those which appear in a selected playlist. Since the playlist
        filter field is a ModelChoiceFilter, the "value" is the playlist object itself.

        """
        return queryset.filter(id__in=value.media_items)


class MediaItemListView(MediaItemListMixin, generics.ListCreateAPIView):
    """
    Endpoint to retrieve a list of media.

    """
    filter_backends = (filters.OrderingFilter, MediaItemListSearchFilter,
                       df_filters.DjangoFilterBackend)
    ordering = '-publishedAt'
    ordering_fields = ('publishedAt',)
    pagination_class = ListPagination
    search_fields = ('title', 'description', 'tags')
    serializer_class = serializers.MediaItemSerializer
    filterset_class = MediaItemFilter

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(publishedAt=models.F('published_at'))


class MediaItemView(MediaItemMixin, generics.RetrieveUpdateAPIView):
    """
    Endpoint to retrieve a single media item.

    """
    serializer_class = serializers.MediaItemDetailSerializer


class MediaItemUploadView(MediaItemMixin, generics.RetrieveUpdateAPIView):
    """
    Endpoint for retrieving an upload URL for a media item. Requires that the user have the edit
    permission for the media item. Should the upload URL be expired or otherwise unsuitable, a HTTP
    POST/PUT to this endpoint refreshes the URL.

    """
    # To access the upload API, the user must always have the edit permission.
    permission_classes = MediaItemListMixin.permission_classes + [
        permissions.MediaPlatformEditPermission
    ]
    serializer_class = serializers.MediaUploadSerializer

    # Make sure that the related upload_endpoint is fetched by the queryset
    def get_queryset(self):
        return super().get_queryset().select_related('upload_endpoint')


class MediaItemEmbedViewInspector(inspectors.ViewInspector):
    def get_operation(self, operation_keys):
        return openapi.Operation(
            operation_id='media_embed',
            responses=openapi.Responses(
                {302: openapi.Response(description='Media embed page')}
            ),
            tags=['media'],
        )


class MediaItemEmbedView(MediaItemMixin, generics.RetrieveAPIView):
    """
    Endpoint to retrieve a media item as an embedded IFrame.

    """
    swagger_schema = MediaItemEmbedViewInspector

    def retrieve(self, request, *args, **kwargs):
        item = self.get_object()
        if not hasattr(item, 'jwp'):
            raise Http404()
        return render(request, 'api/embed_js.html', {
            'media_item': item,
            'embed_code': item.jwp.embed_url(format='js'),
            'player_id': settings.JWPLATFORM_EMBED_PLAYER_KEY
        })


class MediaItemSourceViewInspector(inspectors.ViewInspector):
    def get_operation(self, operation_keys):
        return openapi.Operation(
            operation_id='media_source',
            responses=openapi.Responses(
                {302: openapi.Response(description='Media source stream')}
            ),
            parameters=[
                openapi.Parameter(
                    name='mimeType', in_=openapi.IN_QUERY,
                    description='MIME type of media source',
                    type=openapi.TYPE_STRING
                ),
                openapi.Parameter(
                    name='width', in_=openapi.IN_QUERY,
                    description='Width of media source',
                    type=openapi.TYPE_INTEGER
                ),
                openapi.Parameter(
                    name='height', in_=openapi.IN_QUERY,
                    description='Height of media source',
                    type=openapi.TYPE_INTEGER
                ),
            ],
            tags=['media'],
        )


class MediaItemSourceView(MediaItemMixin, generics.RetrieveAPIView):
    """
    Endpoint to retrieve a media item source stream

    """
    swagger_schema = MediaItemSourceViewInspector

    def retrieve(self, request, *args, **kwargs):
        item = self.get_object()

        # Check if user can download media item
        if not item.downloadable_by_user:
            raise Http404()

        mime_type = request.GET.get('mimeType')
        width = request.GET.get('width')
        height = request.GET.get('height')

        try:
            if width is not None:
                width = int(width)
            if height is not None:
                height = int(height)
        except ValueError:
            raise ParseError()

        if mime_type is None and width is None and height is None:
            # If nothing was specified, return the "best" source.
            video_sources = [
                source for source in item.sources
                if source.mime_type.startswith('video/') and source.height is not None
            ]
            audio_sources = [
                source for source in item.sources
                if source.mime_type.startswith('audio/')
            ]

            if len(video_sources) == 0 and len(audio_sources) != 0:
                # No video sources, return any of the audio sources
                return redirect(audio_sources.pop().url)
            elif len(video_sources) != 0:
                # Sort videos by descending height
                return redirect(sorted(video_sources, key=lambda s: -s.height)[0].url)
        else:
            for source in item.sources:
                if (source.mime_type == mime_type and source.width == width
                        and source.height == height):
                    return redirect(source.url)

        raise Http404()


class MediaItemAnalyticsView(MediaItemMixin, generics.RetrieveAPIView):
    """
    Endpoint to retrieve the analytics for a single media item.

    """
    serializer_class = serializers.MediaItemAnalyticsListSerializer


class ChannelListMixin(ListMixinBase):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for listing
    (and possibly creating/deleting) channels. Use this mixin with ListAPIView or
    ListCreateAPIView to form a concrete view class.

    """
    queryset = mpmodels.Channel.objects


class ChannelMixin(ChannelListMixin):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for
    retrieving (and possibly updating) individual channels. Use this mixin with RetrieveAPIView
    or RetrieveUpdateAPIView to form a concrete view class.

    """


class ChannelListFilterSet(df_filters.FilterSet):
    class Meta:
        model = mpmodels.Channel
        fields = ('editable',)

    editable = df_filters.BooleanFilter(
        label='Editable', help_text='Filter by whether the user can edit this channel')


class ChannelListView(ChannelListMixin, generics.ListCreateAPIView):
    """
    Endpoint to retrieve a list of channels.

    """
    filter_backends = (
        filters.OrderingFilter, filters.SearchFilter, df_filters.DjangoFilterBackend)
    ordering = '-createdAt'
    ordering_fields = ('createdAt', 'title')
    pagination_class = ListPagination
    search_fields = ('title', 'description')
    serializer_class = serializers.ChannelSerializer
    filterset_class = ChannelListFilterSet

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(createdAt=models.F('created_at'))


class ChannelView(ChannelMixin, generics.RetrieveUpdateAPIView):
    """
    Endpoint to retrieve an individual channel.

    """
    serializer_class = serializers.ChannelDetailSerializer

    def get_queryset(self):
        return annotate_channel_qs_for_detail(super().get_queryset(), user=self.request.user)


class PlaylistListMixin(ListMixinBase):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for listing
    (and possibly creating/deleting) playlists. Use this mixin with ListAPIView or
    ListCreateAPIView to form a concrete view class.

    """
    queryset = mpmodels.Playlist.objects


class PlaylistMixin(PlaylistListMixin):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for
    retrieving (and possibly updating) individual playlists. Use this mixin with RetrieveAPIView
    or RetrieveUpdateAPIView to form a concrete view class.

    """


class PlaylistListFilterSet(df_filters.FilterSet):
    class Meta:
        model = mpmodels.Playlist
        fields = ('editable',)

    editable = df_filters.BooleanFilter(
        label='Editable', help_text='Filter by whether the user can edit this channel')


class PlaylistListView(PlaylistListMixin, generics.ListCreateAPIView):
    """
    Endpoint to retrieve a list of playlists.

    """
    filter_backends = (
        filters.OrderingFilter, filters.SearchFilter, df_filters.DjangoFilterBackend)
    ordering = '-updatedAt'
    ordering_fields = ('updatedAt', 'createdAt', 'title')
    pagination_class = ListPagination
    search_fields = ('title', 'description')
    serializer_class = serializers.PlaylistSerializer
    filter_fields = ('channel',)
    filterset_class = PlaylistListFilterSet

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(createdAt=models.F('created_at'), updatedAt=models.F('updated_at'))


class PlaylistView(PlaylistMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint to retrieve an individual playlists.

    """
    serializer_class = serializers.PlaylistDetailSerializer


def exception_handler(exc, context):
    """
    A custom exception handler which handles 404s on embed views by rendering a template which
    suggests the user log in.

    """
    view = context['view'] if 'view' in context else None
    if not isinstance(view, MediaItemEmbedView) or not isinstance(exc, Http404):
        return views.exception_handler(exc, context)

    new_context = {
        'settings': settings,
        'login_url': '%s?next=%s' % (settings.LOGIN_URL, context['request'].get_full_path()),
    }
    new_context.update(context)
    return render(context['request'], 'api/embed_404.html', status=404, context=new_context)
