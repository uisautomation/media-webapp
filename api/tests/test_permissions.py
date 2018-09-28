from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

import mediaplatform.models as mpmodels

from .. import permissions


class MediaPlatformPermissionTestCase(TestCase):
    fixtures = ['api/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        self.factory = APIRequestFactory()
        self.safe_request = self.factory.get('/')
        self.unsafe_request = self.factory.post('/')
        self.item = mpmodels.MediaItem.objects.get(id='empty')
        self.permission = permissions.MediaPlatformPermission()
        self.view = None  # if MediaPlatformPermission start using this, we need to set it
        self.user = get_user_model().objects.first()
        self.assertIsNotNone(self.user)

        lookup_patcher = mock.patch('mediaplatform.models._lookup_groupids_and_instids_for_user')
        self.lookup_groupids_and_instids_for_user = lookup_patcher.start()
        self.addCleanup(lookup_patcher.stop)
        self.lookup_groupids_and_instids_for_user.return_value = ([], [])

    def test_safe_allowed_in_general(self):
        self.assert_safe_has_permission()

    def test_unsafe_not_allowed_in_general(self):
        self.assert_unsafe_does_not_have_permission()

    def test_safe_requires_viewable_object(self):
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()

        self.item.view_permission.reset()
        self.item.view_permission.save()

        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertFalse(item.viewable)
        self.assertFalse(item.editable)
        self.assert_safe_object_does_not_have_permission(item)
        self.item.view_permission.is_public = True
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertFalse(item.editable)
        self.assert_safe_object_has_permission(item)
        self.item.channel.edit_permission.is_public = True
        self.item.channel.edit_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertTrue(item.editable)
        self.assert_unsafe_object_has_permission(item)

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_unsafe_object_has_permission(self.fetch_item(annotate_editable=True))

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_unsafe_object_has_permission(self.fetch_item(annotate_viewable=True))

    def test_unsafe_requires_editable_object(self):
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()

        self.item.view_permission.reset()
        self.item.view_permission.save()

        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertFalse(item.viewable)
        self.assertFalse(item.editable)
        self.assert_unsafe_object_does_not_have_permission(item)
        self.item.view_permission.is_public = True
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertFalse(item.editable)
        self.assert_unsafe_object_does_not_have_permission(item)
        self.item.channel.edit_permission.is_public = True
        self.item.channel.edit_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertTrue(item.editable)
        self.assert_unsafe_object_has_permission(item)

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_unsafe_object_has_permission(self.fetch_item(annotate_editable=True))

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_unsafe_object_has_permission(self.fetch_item(annotate_viewable=True))

    def assert_safe_has_permission(self):
        self.assertTrue(self.permission.has_permission(self.safe_request, self.view))

    def assert_safe_does_not_have_permission(self):
        self.assertFalse(self.permission.has_permission(self.safe_request, self.view))

    def assert_unsafe_has_permission(self):
        self.assertTrue(self.permission.has_permission(self.unsafe_request, self.view))

    def assert_unsafe_does_not_have_permission(self):
        self.assertFalse(self.permission.has_permission(self.unsafe_request, self.view))

    def assert_safe_object_has_permission(self, obj):
        self.assertTrue(self.permission.has_object_permission(self.safe_request, self.view, obj))

    def assert_safe_object_does_not_have_permission(self, obj):
        self.assertFalse(self.permission.has_object_permission(self.safe_request, self.view, obj))

    def assert_unsafe_object_has_permission(self, obj):
        self.assertTrue(self.permission.has_object_permission(self.unsafe_request, self.view, obj))

    def assert_unsafe_object_does_not_have_permission(self, obj):
        self.assertFalse(self.permission.has_object_permission(
            self.unsafe_request, self.view, obj))

    def fetch_item(self, annotate_viewable=False, annotate_editable=False):
        qs = mpmodels.MediaItem.objects.all()
        if annotate_viewable:
            qs = qs.annotate_viewable(self.user)
        if annotate_editable:
            qs = qs.annotate_editable(self.user)
        return qs.get(id=self.item.id)


class MediaPlatformEditPermissionTestCase(MediaPlatformPermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = permissions.MediaPlatformEditPermission()

    def test_safe_requires_viewable_object(self):
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()

        self.item.view_permission.reset()
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertFalse(item.viewable)
        self.assertFalse(item.editable)
        self.assert_safe_object_does_not_have_permission(item)
        self.item.view_permission.is_public = True
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertFalse(item.editable)
        self.assert_safe_object_does_not_have_permission(item)
        self.item.channel.edit_permission.is_public = True
        self.item.channel.edit_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertTrue(item.editable)
        self.assert_safe_object_has_permission(item)

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_safe_object_has_permission(self.fetch_item(annotate_viewable=True))

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_safe_object_has_permission(self.fetch_item(annotate_editable=True))

    def test_unsafe_requires_editable_object(self):
        self.item.channel.edit_permission.reset()
        self.item.channel.edit_permission.save()

        self.item.view_permission.reset()
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertFalse(item.viewable)
        self.assertFalse(item.editable)
        self.assert_unsafe_object_does_not_have_permission(item)
        self.item.view_permission.is_public = True
        self.item.view_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertFalse(item.editable)
        self.assert_unsafe_object_does_not_have_permission(item)
        self.item.channel.edit_permission.is_public = True
        self.item.channel.edit_permission.save()
        item = self.fetch_item(annotate_viewable=True, annotate_editable=True)
        self.assertTrue(item.viewable)
        self.assertTrue(item.editable)
        self.assert_unsafe_object_has_permission(item)

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_safe_object_has_permission(self.fetch_item(annotate_viewable=True))

        with self.assertRaises(permissions.ObjectNotAnnotated):
            self.assert_safe_object_has_permission(self.fetch_item(annotate_editable=True))
