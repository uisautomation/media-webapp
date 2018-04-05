"""
Module providing lookup API-related functionality.

"""
from urllib.parse import urljoin
from django.conf import settings
from django.core.cache import cache

from .oauth2client import AuthenticatedSession


#: An authenticated session which can access the lookup API
LOOKUP_SESSION = AuthenticatedSession(scopes=settings.SMS_OAUTH2_LOOKUP_SCOPES)


def get_person_for_user(user):
    """
    Return the resource from Lookup associated with the specified user. A requests package
    :py:class:`HTTPError` is raised if the request fails.

    The result of this function call is cached based on the username so it is safe to call this
    multiple times.

    If user is the anonymous user (user.is_anonymous is True), :py:class:`~.UserIsAnonymousError`
    is raised.

    """
    # check that the user is not anonymous
    if user.is_anonymous:
        raise RuntimeError('User is anonymous')

    # return a cached response if we have it
    cached_resource = cache.get(f"{user.username}:lookup")
    if cached_resource is not None:
        return cached_resource

    # Ask lookup about this person
    lookup_response = LOOKUP_SESSION.request(
        method='GET', url=urljoin(
            settings.LOOKUP_ROOT,
            f'people/{settings.LOOKUP_PEOPLE_ID_SCHEME}/{user.username}?fetch=all_insts,all_groups'
        )
    )

    # Raise if there was an error
    lookup_response.raise_for_status()

    # save cached value
    cache.set(f"{user.username}:lookup", lookup_response.json(),
              settings.LOOKUP_PEOPLE_CACHE_LIFETIME)

    # recurse, which should now retrieve the value from the cache
    return get_person_for_user(user)
