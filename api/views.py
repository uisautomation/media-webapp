"""
Views implementing the API endpoints.

"""
import logging

from django.db import models
from django_filters import rest_framework as df_filters
from rest_framework import generics, pagination, filters

import mediaplatform.models as mpmodels

from . import permissions
from . import serializers


LOG = logging.getLogger(__name__)


class ProfileView(generics.RetrieveAPIView):
    """
    Endpoint to retrieve the profile of the current user.

    """
    serializer_class = serializers.ProfileSerializer

    def get_object(self):
        return self.request.user


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
    view's ``search_fields`` attribute, then the tags field is dearched for any tag matching the
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
            .select_related('jwp')
        )


class MediaItemMixin(MediaItemListMixin):
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for
    retrieving (and possibly updating) individual media items. Use this mixin with RetrieveAPIView
    or RetrieveUpdateAPIView to form a concrete view class.

    """


class MediaItemListView(MediaItemListMixin, generics.ListCreateAPIView):
    """
    Endpoint to retrieve a list of media.

    """
    filter_backends = (
        filters.OrderingFilter, MediaItemListSearchFilter, df_filters.DjangoFilterBackend)
    ordering = '-publishedAt'
    ordering_fields = ('publishedAt',)
    pagination_class = ListPagination
    search_fields = ('title', 'description', 'tags')
    serializer_class = serializers.MediaItemSerializer
    filterset_fields = ('channel',)

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
