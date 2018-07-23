from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import TestCase, override_settings

from .. import models


User = get_user_model()


class MediaItemTest(TestCase):
    fixtures = ['mediaplatform/tests/fixtures/test_data.yaml']

    def setUp(self):
        self.user = User.objects.get(username='testuser')

        self.lookup_groupids_and_instids_for_user_patcher = mock.patch(
                'mediaplatform.models._lookup_groupids_and_instids_for_user')
        self.lookup_groupids_and_instids_for_user = (
            self.lookup_groupids_and_instids_for_user_patcher.start())
        self.lookup_groupids_and_instids_for_user.return_value = ([], [])
        self.addCleanup(self.lookup_groupids_and_instids_for_user_patcher.stop)

    def test_creation(self):
        """A MediaItem object should be creatable with no field values."""
        models.MediaItem.objects.create()

    def test_no_deleted_in_objects(self):
        """The default queryset used by MediaItem.objects contains no deleted items."""
        self.assertEqual(models.MediaItem.objects.filter(deleted_at__isnull=False).count(), 0)

    def test_deleted_in_objects_including_deleted(self):
        """If we explicitly ask for deleted objects, we get them."""
        self.assertGreater(
            models.MediaItem.objects_including_deleted.filter(deleted_at__isnull=False).count(), 0)

    def test_public_item_viewable_by_anon(self):
        """The public video is viewable by anonymous."""
        self.assert_user_can_view(AnonymousUser(), 'public')

    def test_signed_in_item_not_viewable_by_anon(self):
        """The signed in video is not viewable by anonymous."""
        self.assert_user_cannot_view(AnonymousUser(), 'signedin')

    def test_user_of_none_is_treated_as_anon(self):
        """
        If a user of "None" is passed to viewable_by_user(), it is treated as the anonymous user.
        """
        self.assert_user_can_view(None, 'public')
        self.assert_user_cannot_view(None, 'signedin')

    def test_signed_in_item_viewable_by_signed_in(self):
        self.assert_user_can_view(self.user, 'signedin')

    def test_public_item_viewable_by_signed_in(self):
        self.assert_user_can_view(self.user, 'public')

    def test_item_with_no_perms_not_viewable(self):
        """An item with empty permissions is not viewable by the anonymous or signed in user."""
        self.assert_user_cannot_view(AnonymousUser(), 'emptyperm')
        self.assert_user_cannot_view(self.user, 'emptyperm')

    def test_item_with_matching_crsid_viewable(self):
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_view(self.user, item)
        item.view_permission.crsids.extend(['spqr1', self.user.username, 'abcd1'])
        item.view_permission.save()
        self.assert_user_can_view(self.user, item)

    def test_item_with_matching_lookup_groups_viewable(self):
        """
        A user who has at least one lookup group which is in the set of lookup groups for a media
        item can view it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = ['A', 'B', 'C'], []
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_view(self.user, item)
        item.view_permission.lookup_groups.extend(['X', 'Y', 'A', 'B', 'Z'])
        item.view_permission.save()
        self.assert_user_can_view(self.user, item)

    def test_item_with_matching_lookup_insts_viewable(self):
        """
        A user who has at least one lookup institution which is in the set of lookup institutions
        for a media item can view it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = [], ['A', 'B', 'C']
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_view(self.user, item)
        item.view_permission.lookup_insts.extend(['X', 'Y', 'A', 'B', 'Z'])
        item.view_permission.save()
        self.assert_user_can_view(self.user, item)

    def test_view_permission_created(self):
        """A new MediaItem has a view permission created on save()."""
        item = models.MediaItem.objects.create()
        self.assertIsNotNone(models.MediaItem.objects.get(id=item.id).view_permission)

    def test_view_permission_not_re_created(self):
        """The view_permission is not changes if a MediaItem is updated."""
        item = models.MediaItem.objects.create()
        permission_id_1 = models.MediaItem.objects.get(id=item.id).view_permission.id
        item = models.MediaItem.objects.get(id=item.id)
        item.title = 'changed'
        item.save()
        permission_id_2 = models.MediaItem.objects.get(id=item.id).view_permission.id
        self.assertEquals(permission_id_1, permission_id_2)

    def test_edit_permission_created(self):
        """A new MediaItem has a edit permission created on save()."""
        item = models.MediaItem.objects.create()
        self.assertIsNotNone(models.MediaItem.objects.get(id=item.id).edit_permission)

    def test_edit_permission_not_re_created(self):
        """The edit_permission is not changes if a MediaItem is updated."""
        item = models.MediaItem.objects.create()
        permission_id_1 = models.MediaItem.objects.get(id=item.id).edit_permission.id
        item = models.MediaItem.objects.get(id=item.id)
        item.title = 'changed'
        item.save()
        permission_id_2 = models.MediaItem.objects.get(id=item.id).edit_permission.id
        self.assertEquals(permission_id_1, permission_id_2)

    def assert_user_cannot_view(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = models.MediaItem.objects_including_deleted.get(id=item_or_id)
        self.assertFalse(
            models.MediaItem.objects_including_deleted.all()
            .filter(id=item_or_id.id)
            .viewable_by_user(user)
            .exists()
        )
        self.assertFalse(
            models.MediaItem.objects_including_deleted.all()
            .annotate_viewable(user, name='TEST_viewable')
            .get(id=item_or_id.id)
            .TEST_viewable
        )

    def assert_user_can_view(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = models.MediaItem.objects_including_deleted.get(id=item_or_id)
        self.assertTrue(
            models.MediaItem.objects.all().viewable_by_user(user).filter(id=item_or_id.id).exists()
        )
        self.assertTrue(
            models.MediaItem.objects_including_deleted.all()
            .annotate_viewable(user, name='TEST_viewable')
            .get(id=item_or_id.id)
            .TEST_viewable
        )


class CollectionTest(TestCase):
    def test_creation(self):
        """A Collection object should be creatable with no field values."""
        models.Collection.objects.create()

    def test_view_permission_created(self):
        """A new Collection has a view permission created on save()."""
        item = models.Collection.objects.create()
        self.assertIsNotNone(models.Collection.objects.get(id=item.id).view_permission)

    def test_view_permission_not_re_created(self):
        """The view_permission is not changes if a Collection is updated."""
        item = models.Collection.objects.create()
        permission_id_1 = models.Collection.objects.get(id=item.id).view_permission.id
        item = models.Collection.objects.get(id=item.id)
        item.title = 'changed'
        item.save()
        permission_id_2 = models.Collection.objects.get(id=item.id).view_permission.id
        self.assertEquals(permission_id_1, permission_id_2)

    def test_edit_permission_created(self):
        """A new Collection has a edit permission created on save()."""
        item = models.Collection.objects.create()
        self.assertIsNotNone(models.Collection.objects.get(id=item.id).edit_permission)

    def test_edit_permission_not_re_created(self):
        """The edit_permission is not changes if a MediaItem is updated."""
        item = models.MediaItem.objects.create()
        permission_id_1 = models.MediaItem.objects.get(id=item.id).edit_permission.id
        item = models.MediaItem.objects.get(id=item.id)
        item.title = 'changed'
        item.save()
        permission_id_2 = models.MediaItem.objects.get(id=item.id).edit_permission.id
        self.assertEquals(permission_id_1, permission_id_2)


class PermissionTest(TestCase):
    def test_creation(self):
        """A Permission object should be creatable with no field values."""
        models.Permission.objects.create()


class LookupTest(TestCase):
    PERSON_FIXTURE = {
        'groups': [
            {'groupid': '0123'},
            {'groupid': '4567'},
        ],
        'institutions': [
            {'instid': 'DEPTA'},
            {'instid': 'OFFICEB'},
        ],
    }

    def setUp(self):
        self.get_person_patcher = mock.patch('automationlookup.get_person')
        self.get_person = self.get_person_patcher.start()
        self.get_person.return_value = self.PERSON_FIXTURE
        self.addCleanup(self.get_person_patcher.stop)

        self.user = User.objects.create(username='testuser')

        # Make sure the Django cache is empty when running tests
        cache.clear()

    def test_basic_groups_functionality(self):
        expected_groupids = [
            g['groupid'] for g in self.PERSON_FIXTURE['groups']
        ]
        groups, _ = models._lookup_groupids_and_instids_for_user(self.user)
        self.assertEqual(groups, expected_groupids)

    def test_basic_institutions_functionality(self):
        expected_instids = [
            g['instid'] for g in self.PERSON_FIXTURE['institutions']
        ]
        _, insts = models._lookup_groupids_and_instids_for_user(self.user)
        self.assertEqual(insts, expected_instids)

    @override_settings(LOOKUP_SCHEME='noscheme')
    def test_calls_get_person(self):
        """get_person is called correctly"""
        models._lookup_groupids_and_instids_for_user(self.user)
        self.get_person.assert_called_once_with(
            identifier=self.user.username, scheme=settings.LOOKUP_SCHEME,
            fetch=['all_groups', 'all_insts'])
