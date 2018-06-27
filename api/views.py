"""
Views implementing the API endpoints.

"""
import copy
import logging

from django.db.models import Q
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from smsjwplatform import jwplatform
from smsjwplatform.models import CachedResource

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


class CollectionListView(APIView):
    """
    Endpoint to retrieve a list of collections.

    """
    @swagger_auto_schema(
        query_serializer=serializers.CollectionListQuerySerializer(),
        responses={200: serializers.CollectionListSerializer()}
    )
    def get(self, request):
        """Handle GET request."""
        client = jwplatform.get_jwplatform_client()

        query_serializer = serializers.CollectionListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        params = {}

        # Add default parameters
        params.update({
            'result_limit': 100,
        })

        # Add parameters from query
        for key in ['search']:
            if query_serializer.data.get(key) is not None:
                params[key] = query_serializer.data[key]

        # Add parameters which cannot be overridden
        params.update({
            'http_method': 'POST',
        })

        # Create a shallow copy of the response because we modify it below
        channel_list = copy.copy(check_api_call(jwplatform.Channel.list(params, client=client)))

        # Filter channels. They must have an SMS collection id (so have originated on the SMS).
        channel_list['channels'] = [
            channel for channel in channel_list['channels']
            if channel.collection_id is not None
        ]

        # TODO: filter channels by ACL - there is currently no processing of channel ACLs by the
        # sms2jwplayer scripts.

        return Response(serializers.CollectionListSerializer(channel_list).data)


class MediaListView(APIView):
    """
    Endpoint to retrieve a list of media.

    """
    # Mapping from order_by values to SQL expression giving the appropriate value to order results
    # by.
    ORDER_BY_MAP = {
        'date': "data -> 'date'",
    }

    @swagger_auto_schema(
        query_serializer=serializers.MediaListQuerySerializer(),
        responses={200: serializers.MediaListSerializer()}
    )
    def get(self, request):
        """Handle GET request."""
        query_serializer = serializers.MediaListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query = query_serializer.data

        limit, offset = 100, 0

        # Django has limited understanding of how to order by a JSONField so we help it out a bit
        # here by using the .extra() method on the QuerySet and just providing the SQL expression
        # directly.
        # Django will have native support for order_by in JSONFields from Django 2.1
        # To keep track of the issue: https://code.djangoproject.com/ticket/24747
        videos = CachedResource.videos.extra(
            select={'__ordering': self.ORDER_BY_MAP[query['order_by']]},
            order_by=[
                '{}__ordering'.format('-' if query['direction'] == 'desc' else '')
            ]
        )

        # If the search field is populated, match on title and description. We can be cleverer here
        # and, for example, use Postgres' support for full text search:
        # https://www.postgresql.org/docs/current/static/textsearch.html
        search = query.get('search')
        if search is not None:
            videos = videos.filter(
                Q(data__title__icontains=search) |
                Q(data__description__icontains=search)
            )

        # Filter videos. They must have a) an SMS media id (so have originated on the SMS) and b)
        # have an ACL which allows the current user.
        video_list = [jwplatform.Video(video.data) for video in videos.all()[offset:offset+limit]]
        response = {
            'videos': [
                video for video in video_list
                if video.media_id is not None and user_can_view_resource(request.user, video)
            ],
            'limit': limit,
            'offset': offset,
            'total': videos.count(),
        }

        return Response(serializers.MediaListSerializer(response).data)


def user_can_view_resource(user, resource):
    """
    Return a boolean indicating if the passed Django user can access the passed JWPlatform
    resource. The decision is based on the ACLs associated with the resource.

    """
    try:
        resource.check_user_access(user)
        return True
    except jwplatform.ResourceACLPermissionDenied:
        return False
