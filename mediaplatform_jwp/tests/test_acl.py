"""
Tests for :py:mod:acl
"""
from unittest import mock

from django.test import TestCase

from mediaplatform_jwp.acl import AceWorld, AceCam, AceInst, AceGroup, AceUser, build_acl


class AclTest(TestCase):
    """
    General module tests
    """
    def test_build_acl(self):

        result = build_acl(['WORLD', 'CAM', 'INST_UIS', 'GROUP_59739', 'USER_mb2174'])

        self.assertIsInstance(result[0], AceWorld)
        self.assertIsInstance(result[1], AceCam)
        self.assertIsInstance(result[2], AceInst)
        self.assertEqual(result[2].instid, 'UIS')
        self.assertIsInstance(result[3], AceGroup)
        self.assertEqual(result[3].groupid, '59739')
        self.assertIsInstance(result[4], AceUser)
        self.assertEqual(result[4].crsid, 'mb2174')

        with self.assertRaises(AssertionError):
            build_acl(['OTHER'])


class AceWorldTest(TestCase):
    """
    Tests for :py:class:AceWorld
    """
    def test_parse(self):
        self.assertIsInstance(AceWorld.parse('WORLD'), AceWorld)
        self.assertIsNone(AceWorld.parse('CAM'))
        self.assertIsNone(AceWorld.parse('INST_UIS'))
        self.assertIsNone(AceWorld.parse('GROUP_59739'))
        self.assertIsNone(AceWorld.parse('USER_mb2174'))

    def test_has_permission(self):
        self.assertTrue(AceWorld().has_permission(mock.Mock()))


class AceCamTest(TestCase):
    """
    Tests for :py:class:AceCam
    """
    def test_parse(self):
        self.assertIsNone(AceCam.parse('WORLD'))
        self.assertIsInstance(AceCam.parse('CAM'), AceCam)
        self.assertIsNone(AceCam.parse('INST_UIS'))
        self.assertIsNone(AceCam.parse('GROUP_59739'))
        self.assertIsNone(AceCam.parse('USER_mb2174'))

    def test_has_permission(self):
        ace_cam = AceCam()
        self.assertFalse(ace_cam.has_permission(mock.Mock(is_anonymous=True)))
        self.assertTrue(ace_cam.has_permission(mock.Mock(is_anonymous=False)))


class AceInstTest(TestCase):
    """
    Tests for :py:class:ceInst
    """
    def test_parse(self):
        self.assertIsNone(AceInst.parse('WORLD'))
        self.assertIsNone(AceInst.parse('CAM'))
        ace_inst = AceInst.parse('INST_UIS')
        self.assertIsInstance(ace_inst, AceInst)
        self.assertEqual(ace_inst.instid, 'UIS')
        self.assertIsNone(AceInst.parse('GROUP_59739'))
        self.assertIsNone(AceInst.parse('USER_mb2174'))

    def test_has_permission(self):
        patch_get_person(self)
        user = mock.Mock(is_anonymous=False)

        self.assertTrue(AceInst('UIS').has_permission(user))
        self.assertFalse(AceInst('CL').has_permission(user))


class AceGroupTest(TestCase):
    """
    Tests for :py:class:AceGroup
    """
    def test_parse(self):
        self.assertIsNone(AceGroup.parse('WORLD'))
        self.assertIsNone(AceGroup.parse('CAM'))
        self.assertIsNone(AceGroup.parse('INST_UIS'))
        ace_group = AceGroup.parse('GROUP_59739')
        self.assertIsInstance(ace_group, AceGroup)
        self.assertEqual(ace_group.groupid, '59739')
        self.assertIsNone(AceInst.parse('USER_mb2174'))

    def test_has_permission(self):
        patch_get_person(self)
        user = mock.Mock(is_anonymous=False)

        self.assertTrue(AceGroup('12345').has_permission(user))
        self.assertTrue(AceGroup('uis-members').has_permission(user))
        self.assertFalse(AceGroup('99999').has_permission(user))


class AceUserTest(TestCase):
    """
    Tests for :py:class:AceUser
    """
    def test_parse(self):
        self.assertIsNone(AceUser.parse('WORLD'))
        self.assertIsNone(AceUser.parse('CAM'))
        self.assertIsNone(AceUser.parse('INST_UIS'))
        self.assertIsNone(AceUser.parse('GROUP_59739'))
        ace_user = AceUser.parse('USER_mb2174')
        self.assertIsInstance(ace_user, AceUser)
        self.assertEqual(ace_user.crsid, 'mb2174')

    def test_has_permission(self):
        ace_user = AceUser("mb2174")
        self.assertFalse(ace_user.has_permission(mock.Mock(username="rjw57")))
        self.assertTrue(ace_user.has_permission(mock.Mock(username="mb2174")))


def patch_get_person(self):
    get_person = mock.Mock()
    get_person.return_value = {
        'institutions': [{'instid': 'UIS'}],
        'groups': [{'groupid': '12345', 'name': 'uis-members'}]
    }
    patcher = mock.patch('automationlookup.get_person', get_person)
    self.addCleanup(patcher.stop)
    patcher.start()
