"""
Module providing lookup API-related functionality.

"""
import logging
from urllib.parse import urljoin
from django.conf import settings
from django.core.cache import cache

from .oauth2client import AuthenticatedSession

LOG = logging.getLogger(__name__)


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


class AceWorld:
    """FIXME"""

    @staticmethod
    def parse(ace):
        return AceWorld() if ace == 'WORLD' else None

    @staticmethod
    def has_permission(user):
        return True


class AceCam:
    """FIXME"""

    @staticmethod
    def parse(ace):
        return AceCam() if ace == 'CAM' else None

    @staticmethod
    def has_permission(user):
        return not user.is_anonymous


class AceInst:
    """FIXME"""
    prefix = 'INST_'

    def __init__(self, instid):
        self.instid = instid

    @staticmethod
    def parse(ace):
        if ace.startswith(AceInst.prefix):
            return AceInst(ace[len(AceInst.prefix):])
        return None

    def has_permission(self, user):
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response['institutions']:
            if self.instid == institution['instid']:
                return True
        return False


class AceGroup:
    """FIXME"""
    prefix = 'GROUP_'

    def __init__(self, groupid):
        self.groupid = groupid

    @staticmethod
    def parse(ace):
        if ace.startswith(AceGroup.prefix):
            return AceGroup(ace[len(AceGroup.prefix):])
        return None

    def has_permission(self, user):
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response['groups']:
            if self.groupid == institution['groupid'] or self.groupid == institution['name']:
                return True
        return False


class AceUser:
    """FIXME"""
    prefix = 'USER_'

    def __init__(self, crsid):
        self.crsid = crsid

    @staticmethod
    def parse(ace):
        if ace.startswith(AceUser.prefix):
            return AceUser(ace[len(AceUser.prefix):])
        return None

    def has_permission(self, user):
        return user.username == self.crsid


ACE_TYPES = [AceWorld, AceCam, AceInst, AceGroup, AceUser]


def build_acl(acl):
    acl_ = []
    for ace in acl:
        found = False
        for ace_type in ACE_TYPES:
            ace_ = ace_type.parse(ace)
            if ace_:
                acl_.append(ace_)
                found = True
                break
        assert found, f"'{ace}' not recognised"
    return acl_
