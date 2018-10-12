"""
Custom paginators

"""
from drf_yasg import openapi
from drf_yasg.inspectors import DjangoRestResponsePagination
from rest_framework.compat import coreapi, coreschema
from rest_framework import pagination


class ExtendedCursorPagination(pagination.CursorPagination):
    """
    Custom DRF paginator based on the standard CursorPagination with the extra wrinkle of allowing
    a total object count to be added to the result. By default this parameter is called
    "include_count" and as long as it is set to "true", a count will be returned.

    """
    include_count_query_param = 'include_count'

    def paginate_queryset(self, queryset, request, view=None):
        if self.get_should_include_count(request):
            self.queryset_count = queryset.count()
        else:
            self.queryset_count = None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)

        if self.queryset_count is not None:
            response.data['count'] = self.queryset_count

        return response

    def get_should_include_count(self, request):
        if self.include_count_query_param:
            # This rather odd error handling logic is copied from DRF's implementation of similar
            # methods.
            try:
                value = request.query_params[self.include_count_query_param]
                return str(value).lower() == 'true'
            except (KeyError, ValueError):
                pass
        return False

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        # Explicitly get super class' fields as a list since the API just mandates that they be an
        # iterable.
        fields = list(super().get_schema_fields(view))

        if self.include_count_query_param:
            fields.append(coreapi.Field(
                name=self.include_count_query_param,
                required=False,
                location='query',
                schema=coreschema.Boolean(
                    title='Include count of resources',
                    description=(
                        'Include total resource count in response. '
                        'By default the count is not included for performance reasons.'
                    ),
                ),
            ))

        return fields


class ExtendedCursorPaginationInspector(DjangoRestResponsePagination):
    """
    Inspector for DRF YASG which understands :py:class:`~.ExtendedCursorPagination`. Either add
    this to the `DEFAULT_PAGINATOR_INSPECTORS` setting for drf-yasg or decorate your view:

    .. code::

        from django.utils.decorators import method_decorator
        from drf_yasg import utils as yasg_utils

        # ...

        @method_decorator(name='get', decorator=yasg_utils.swagger_auto_schema(
            paginator_inspectors=[ExtendedCursorPaginationInspector]
        ))
        class MyCountView(ListAPIView):
            pagination_class = ExtendedCursorPagination

    """
    def get_paginated_response(self, paginator, response_schema):
        schema = None
        if isinstance(paginator, ExtendedCursorPagination):
            schema = super().get_paginated_response(paginator, response_schema)
            schema['properties']['count'] = openapi.Schema(type=openapi.TYPE_INTEGER)
        return schema
