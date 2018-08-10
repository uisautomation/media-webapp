"""
Views implementing the API endpoints.

"""
import logging

from django.conf import settings
from django.db import connection
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, pagination, filters

import mediaplatform.models as mpmodels

from . import permissions
from . import serializers


LOG = logging.getLogger(__name__)


class JWPAPIException(APIException):
    """
    DRF :py:exc:`APIException` sub-class which indicates that the request could not be handled
    because the JWPlatform API request failed.

    """
    status_code = 502  # Bad Gateway
    default_detail = 'Bad Gateway'
    default_code = 'jwplatform_api_error'


def check_api_call(response):
    """
    Take a response from a JWPlatform API call and raise :py:exc:`JWPAPIException` if the status
    was not ``ok``.

    """
    if response.get('status') == 'ok':
        return response

    LOG.error('API call error: %r', response)
    raise JWPAPIException()


class ProfileView(APIView):
    """
    Endpoint to retrieve the profile of the current user.

    """
    @swagger_auto_schema(
        responses={200: serializers.ProfileSerializer()}
    )
    def get(self, request):
        """Handle GET request."""
        urls = {'login': settings.LOGIN_URL}
        return Response(serializers.ProfileSerializer({
            'user': request.user, 'urls': urls,
        }).data)


class MediaItemListPagination(pagination.CursorPagination):
    page_size = 50


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


class MediaItemListMixin:
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for listing
    (and possibly creating/deleting) media items. Use this mixin with ListAPIView or
    ListCreateAPIView to form a concrete view class.

    """
    queryset = mpmodels.MediaItem.objects
    permission_classes = [permissions.MediaItemPermission]

    def get_queryset(self):
        return (
            super().get_queryset().all()
            .viewable_by_user(self.request.user)
            .annotate_viewable(self.request.user)
            .annotate_editable(self.request.user)
            .select_related('jwp')
            .select_related('sms')
        )


class MediaItemMixin:
    """
    A mixin class for DRF generic views which has all of the specialisations necessary for
    retrieving (and possibly updating) individual media items. Use this mixin with RetrieveAPIView
    or RetrieveUpdateAPIView to form a concrete view class.

    """
    queryset = mpmodels.MediaItem.objects
    permission_classes = [permissions.MediaItemPermission]

    def get_queryset(self):
        return (
            super().get_queryset().all()
            .viewable_by_user(self.request.user)
            .annotate_viewable(self.request.user)
            .annotate_editable(self.request.user)
            .select_related('jwp')
            .select_related('sms')
        )


class MediaItemListView(MediaItemListMixin, generics.ListCreateAPIView):
    """
    Endpoint to retrieve a list of media.

    """
    filter_backends = (filters.OrderingFilter, MediaItemListSearchFilter)
    ordering = '-published_at'
    ordering_fields = ('published_at',)
    pagination_class = MediaItemListPagination
    search_fields = ('title', 'description', 'tags')
    serializer_class = serializers.MediaItemSerializer


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
        permissions.MediaItemEditPermission
    ]
    serializer_class = serializers.MediaUploadSerializer

    # Make sure that the related upload_endpoint is fetched by the queryset
    def get_queryset(self):
        return super().get_queryset().select_related('upload_endpoint')


class MediaAnalyticsView(APIView):
    """
    Endpoint to retrieve the analytics for a single media item.

    """
    @swagger_auto_schema(
        responses={200: serializers.MediaAnalyticsListSerializer()}
    )
    def get(self, request, pk):
        """Handle GET request."""

        media_item = get_object_or_404(
            mpmodels.MediaItem.objects.filter(pk=pk)
            .viewable_by_user(request.user)
            .select_related('sms')
        )
        results = []
        if hasattr(media_item, 'sms'):
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT day, num_hits FROM stats.media_stats_by_day WHERE media_id=%s",
                    [media_item.sms.id]
                )
                results = cursor.fetchall()
        return Response(serializers.MediaAnalyticsListSerializer(results).data)


def get_cursor():  # pragma: no cover
    """Retrieve DB cursor. Method included for patching in tests"""
    return connection.cursor()
