from automationlookup.models import UserLookup
from django.conf import settings


def user_lookup_middleware(get_response):

    def middleware(request):
        """
        This middleware ensures that a UserLookup model exists
        to map an authenticated user to lookup
        """

        if not request.user.is_anonymous:
            UserLookup.objects.get_or_create(
                user=request.user,
                scheme=settings.LOOKUP_PEOPLE_ID_SCHEME,
                identifier=request.user.username
            )

        return get_response(request)

    return middleware
