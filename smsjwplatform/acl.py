"""
Module providing functionality for handling ACL's stored in the JWPlayer custom property - sms_acl.

"""
import logging

from smsjwplatform.lookup import get_person_for_user

LOG = logging.getLogger(__name__)


class AceWorld:
    """This class encapsulates an ACE of the form WORLD"""

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceWorld if it matches or None if it doesn't"""
        return AceWorld() if ace == 'WORLD' else None

    @staticmethod
    def has_permission(user):
        """Anyone can see the media"""
        LOG.debug('AceWorld.has_permission called with %s', user)
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

    prefix = 'INST_'

    def __init__(self, instid):
        self.instid = instid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceInst if it matches or None if it doesn't"""
        head, prefix, tail = ace.partition(AceInst.prefix)
        return AceInst(tail) if head == '' and prefix == AceInst.prefix else None

    def has_permission(self, user):
        """Only a user belonging to the 'instid' lookup institution can see the media"""
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response.get('institutions', []):
            if self.instid == institution.get('instid', None):
                return True
        return False


class AceGroup:
    """This class encapsulates an ACE of the form GROUP_{groupid}"""

    prefix = 'GROUP_'

    def __init__(self, groupid):
        self.groupid = groupid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceGroup if it matches or None if it doesn't"""
        head, prefix, tail = ace.partition(AceGroup.prefix)
        return AceGroup(tail) if head == '' and prefix == AceGroup.prefix else None

    def has_permission(self, user):
        """Only a user belonging to the 'groupid' lookup group can see the media"""
        if user.is_anonymous:
            return False

        lookup_response = get_person_for_user(user)

        for institution in lookup_response.get('groups', []):
            if self.groupid == institution.get('groupid') or \
                    self.groupid == institution.get('name'):
                return True
        return False


class AceUser:
    """This class encapsulates an ACE of the form USER_{crsid}"""

    prefix = 'USER_'

    def __init__(self, crsid):
        self.crsid = crsid

    @staticmethod
    def parse(ace):
        """Parses an ACE and constructs/return an AceUser if it matches or None if it doesn't"""
        return AceUser(ace[len(AceUser.prefix):]) if ace.startswith(AceUser.prefix) else None

    def has_permission(self, user):
        """Only a user with this CRSID can see the media"""
        return user.username == self.crsid


# this list is used to iterate over all of the Ace classes
ACE_TYPES = [AceWorld, AceCam, AceInst, AceGroup, AceUser]


def build_acl(acl):
    """
    Iterates over the acl and encapsulates each ACE with the corresponding Ace* Class.

    TODO there are performance enhancements that can be made
    (Eg only returning AceWorld, if it exists) but I have kept thing simple for now.

    :param acl: access control list
    :return: list of Ace* objects
    """
    built_acl = []
    for ace in acl:
        found = False
        for ace_type in ACE_TYPES:
            ace_object = ace_type.parse(ace)
            if ace_object:
                built_acl.append(ace_object)
                found = True
                break
        assert found, f"'{ace}' not recognised"
    return built_acl
