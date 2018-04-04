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
    """This class encapsulates an ACE of the form WORLD"""

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceWorld if it matches or None if it doesn't"""
        return AceWorld() if ace == 'WORLD' else None

    @staticmethod
    def has_permission(user):
        """Anyone can see the media"""
        LOG.debug(user)
        return True


class AceCam:
    """This class encapsulates an ACE of the form CAM"""

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceCam if it matches or None if it doesn't"""
        return AceCam() if ace == 'CAM' else None

    @staticmethod
    def has_permission(user):
        """Any authenticated user can see the media"""
        return not user.is_anonymous


class AceInst:
    """This class encapsulates an ACE of the form INST_{instid}"""

    def __init__(self, instid):
        self.instid = instid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceInst if it matches or None if it doesn't"""
        return parse_ace_id('INST_', ace)

    def has_permission(self, user):
        """Only a user belonging to the 'instid' lookup institution can see the media"""
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response['institutions']:
            if self.instid == institution['instid']:
                return True
        return False


class AceGroup:
    """This class encapsulates an ACE of the form GROUP_{groupid}"""

    def __init__(self, groupid):
        self.groupid = groupid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceGroup if it matches or None if it doesn't"""
        return parse_ace_id('GROUP_', ace)

    def has_permission(self, user):
        """Only a user belonging to the 'groupid' lookup group can see the media"""
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response['groups']:
            if self.groupid == institution['groupid'] or self.groupid == institution['name']:
                return True
        return False


class AceUser:
    """This class encapsulates an ACE of the form USER_{crsid}"""

    def __init__(self, crsid):
        self.crsid = crsid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceUser if it matches or None if it doesn't"""
        return parse_ace_id('USER_', ace)

    def has_permission(self, user):
        """Only a user with this CRSID can see the media"""
        return user.username == self.crsid


def parse_ace_id(prefix, ace):
    """This function parses an ACE of the form {prefix}{id} and returns the id."""
    return AceInst(ace[len(prefix):]) if ace.startswith(prefix) else None


# this list is used to iterate over all of the Ace classes
ACE_TYPES = [AceWorld, AceCam, AceInst, AceGroup, AceUser]


def build_acl(acl):
    """
    Iterates over the acl and encapsulates each ACE with the corresponding Ace* Class.

    TODO there are performance enhancements that can be made
    (Eg only returning AceWorld, id it exists) but I have kept thing simple for now.

    :param acl: access control list
    :return: list of Ace* classes
    """
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
