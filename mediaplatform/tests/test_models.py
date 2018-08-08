from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings

from .. import models


User = get_user_model()


class ModelTestCase(TestCase):
    fixtures = ['mediaplatform/tests/fixtures/test_data.yaml']

    def setUp(self):
        self.user = User.objects.get(username='testuser')

        self.lookup_groupids_and_instids_for_user_patcher = mock.patch(
                'mediaplatform.models._lookup_groupids_and_instids_for_user')
        self.lookup_groupids_and_instids_for_user = (
            self.lookup_groupids_and_instids_for_user_patcher.start())
        self.lookup_groupids_and_instids_for_user.return_value = ([], [])
        self.addCleanup(self.lookup_groupids_and_instids_for_user_patcher.stop)

    def assert_user_cannot_view(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = self.model.objects_including_deleted.get(id=item_or_id)
        self.assertFalse(
            self.model.objects_including_deleted.all()
            .filter(id=item_or_id.id)
            .viewable_by_user(user)
            .exists()
        )
        self.assertFalse(
            self.model.objects_including_deleted.all()
            .annotate_viewable(user, name='TEST_viewable')
            .get(id=item_or_id.id)
            .TEST_viewable
        )

    def assert_user_can_view(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = self.model.objects_including_deleted.get(id=item_or_id)
        self.assertTrue(
            self.model.objects.all().viewable_by_user(user).filter(id=item_or_id.id).exists()
        )
        self.assertTrue(
            self.model.objects_including_deleted.all()
            .annotate_viewable(user, name='TEST_viewable')
            .get(id=item_or_id.id)
            .TEST_viewable
        )

    def assert_user_cannot_edit(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = self.model.objects_including_deleted.get(id=item_or_id)
        self.assertFalse(
            self.model.objects_including_deleted.all()
            .filter(id=item_or_id.id)
            .editable_by_user(user)
            .exists()
        )
        self.assertFalse(
            self.model.objects_including_deleted.all()
            .annotate_editable(user, name='TEST_editable')
            .get(id=item_or_id.id)
            .TEST_editable
        )

    def assert_user_can_edit(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = self.model.objects_including_deleted.get(id=item_or_id)
        self.assertTrue(
            self.model.objects.all().editable_by_user(user).filter(id=item_or_id.id).exists()
        )
        self.assertTrue(
            self.model.objects_including_deleted.all()
            .annotate_editable(user, name='TEST_editable')
            .get(id=item_or_id.id)
            .TEST_editable
        )


class MediaItemTest(ModelTestCase):

    model = models.MediaItem

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

    def test_public_item_editable_by_anon(self):
        """An item with public editable permissions is editable by anonymous."""
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_edit(AnonymousUser(), item)
        self.assert_user_cannot_edit(None, item)
        item.channel.edit_permission.is_public = True
        item.channel.edit_permission.save()
        self.assert_user_can_edit(AnonymousUser(), item)
        self.assert_user_can_edit(None, item)

    def test_signed_in_edit_permissions(self):
        """An item with signed in edit permissions is not editable by anonymous."""
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_edit(AnonymousUser(), item)
        self.assert_user_cannot_edit(None, item)
        self.assert_user_cannot_edit(self.user, item)
        item.channel.edit_permission.is_signed_in = True
        item.channel.edit_permission.save()
        self.assert_user_cannot_edit(AnonymousUser(), item)
        self.assert_user_cannot_edit(None, item)
        self.assert_user_can_edit(self.user, item)

    def test_item_with_no_perms_not_editable(self):
        """An item with empty permissions is not editable by the anonymous or signed in user."""
        self.assert_user_cannot_edit(AnonymousUser(), 'emptyperm')
        self.assert_user_cannot_edit(self.user, 'emptyperm')

    def test_item_with_matching_crsid_editable(self):
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_edit(self.user, item)
        item.channel.edit_permission.crsids.extend(['spqr1', self.user.username, 'abcd1'])
        item.channel.edit_permission.save()
        self.assert_user_can_edit(self.user, item)

    def test_item_with_matching_lookup_groups_editable(self):
        """
        A user who has at least one lookup group which is in the set of lookup groups for a media
        item can edit it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = ['A', 'B', 'C'], []
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_edit(self.user, item)
        item.channel.edit_permission.lookup_groups.extend(['X', 'Y', 'A', 'B', 'Z'])
        item.channel.edit_permission.save()
        self.assert_user_can_edit(self.user, item)

    def test_item_with_matching_lookup_insts_editable(self):
        """
        A user who has at least one lookup institution which is in the set of lookup institutions
        for a media item can edit it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = [], ['A', 'B', 'C']
        item = models.MediaItem.objects.get(id='emptyperm')
        self.assert_user_cannot_edit(self.user, item)
        item.channel.edit_permission.lookup_insts.extend(['X', 'Y', 'A', 'B', 'Z'])
        item.channel.edit_permission.save()
        self.assert_user_can_edit(self.user, item)

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

    def assert_user_cannot_edit(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = models.MediaItem.objects_including_deleted.get(id=item_or_id)
        self.assertFalse(
            models.MediaItem.objects_including_deleted.all()
            .filter(id=item_or_id.id)
            .editable_by_user(user)
            .exists()
        )
        self.assertFalse(
            models.MediaItem.objects_including_deleted.all()
            .annotate_editable(user, name='TEST_editable')
            .get(id=item_or_id.id)
            .TEST_editable
        )

    def assert_user_can_edit(self, user, item_or_id):
        if isinstance(item_or_id, str):
            item_or_id = models.MediaItem.objects_including_deleted.get(id=item_or_id)
        self.assertTrue(
            models.MediaItem.objects.all().editable_by_user(user).filter(id=item_or_id.id).exists()
        )
        self.assertTrue(
            models.MediaItem.objects_including_deleted.all()
            .annotate_editable(user, name='TEST_editable')
            .get(id=item_or_id.id)
            .TEST_editable
        )


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


class ChannelTest(ModelTestCase):

    model = models.Channel

    def setUp(self):
        super().setUp()
        self.c1 = models.Channel.objects.get(id='channel1')

    def test_creation_no_fields(self):
        """A Channel object should *not* be creatable with no field values."""
        # TODO this should fail?
        models.Channel.objects.create()

    def test_creation_title_only(self):
        """A Channel object should be creatable with only a title."""
        models.Channel.objects.create(title='XXX')

    def test_no_deleted_in_objects(self):
        """The default queryset used by Channel.objects contains no deleted items."""
        self.assertEqual(models.Channel.objects.filter(deleted_at__isnull=False).count(), 0)

    def test_deleted_in_objects_including_deleted(self):
        """If we explicitly ask for deleted objects, we get them."""
        self.assertGreater(
            models.Channel.objects_including_deleted.filter(deleted_at__isnull=False).count(), 0)

    def test_public_channel_editable_by_anon(self):
        """An channel with public editable permissions is editable by anonymous."""
        self.assert_user_cannot_edit(AnonymousUser(), self.c1)
        self.assert_user_cannot_edit(None, self.c1)
        self.c1.edit_permission.is_public = True
        self.c1.edit_permission.save()
        self.assert_user_can_edit(AnonymousUser(), self.c1)
        self.assert_user_can_edit(None, self.c1)

    def test_signed_in_edit_permissions(self):
        """An channel with signed in edit permissions is not editable by anonymous."""
        self.assert_user_cannot_edit(AnonymousUser(), self.c1)
        self.assert_user_cannot_edit(None, self.c1)
        self.assert_user_cannot_edit(self.user, self.c1)
        self.c1.edit_permission.is_signed_in = True
        self.c1.edit_permission.save()
        self.assert_user_cannot_edit(AnonymousUser(), self.c1)
        self.assert_user_cannot_edit(None, self.c1)
        self.assert_user_can_edit(self.user, self.c1)

    def test_channel_with_no_perms_not_editable(self):
        """An channel with empty permissions is not editable by the anonymous or signed in user."""
        self.c1.edit_permission.reset()
        self.c1.edit_permission.save()
        self.assert_user_cannot_edit(AnonymousUser(), self.c1)
        self.assert_user_cannot_edit(self.user, self.c1)

    def test_channel_with_matching_crsid_editable(self):
        self.assert_user_cannot_edit(self.user, self.c1)
        self.c1.edit_permission.crsids.extend(['spqr1', self.user.username, 'abcd1'])
        self.c1.edit_permission.save()
        self.assert_user_can_edit(self.user, self.c1)

    def test_channel_with_matching_lookup_groups_editable(self):
        """
        A user who has at least one lookup group which is in the set of lookup groups for a media
        self.c1 can edit it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = ['A', 'B', 'C'], []
        self.assert_user_cannot_edit(self.user, self.c1)
        self.c1.edit_permission.lookup_groups.extend(['X', 'Y', 'A', 'B', 'Z'])
        self.c1.edit_permission.save()
        self.assert_user_can_edit(self.user, self.c1)

    def test_channel_with_matching_lookup_insts_editable(self):
        """
        A user who has at least one lookup institution which is in the set of lookup institutions
        for a media self.c1 can edit it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = [], ['A', 'B', 'C']
        self.assert_user_cannot_edit(self.user, self.c1)
        self.c1.edit_permission.lookup_insts.extend(['X', 'Y', 'A', 'B', 'Z'])
        self.c1.edit_permission.save()
        self.assert_user_can_edit(self.user, self.c1)

    def test_edit_permission_created(self):
        """A new Channel has a edit permission created on save()."""
        channel = models.Channel.objects.create(title='test channel')
        self.assertIsNotNone(models.Channel.objects.get(id=channel.id).edit_permission)

    def test_edit_permission_not_re_created(self):
        """The edit_permission is not changed if a Channel is updated."""
        channel = models.Channel.objects.create(title='test channel')
        permission_id_1 = models.Channel.objects.get(id=channel.id).edit_permission.id
        channel = models.Channel.objects.get(id=channel.id)
        channel.title = 'changed'
        channel.save()
        permission_id_2 = models.Channel.objects.get(id=channel.id).edit_permission.id
        self.assertEquals(permission_id_1, permission_id_2)


class PlaylistTest(ModelTestCase):

    model = models.Playlist

    def setUp(self):
        super().setUp()
        self.channel1 = models.Channel.objects.get(id='channel1')

    def test_creation_no_fields(self):
        """A Playlist object should *not* be creatable with no field values."""
        self.assertRaises(IntegrityError, models.Playlist.objects.create)

    def test_creation_minimum_fields(self):
        """A Playlist object should be creatable with a title and a channel."""
        models.Playlist.objects.create(title='XXX', channel=self.channel1)

    def test_no_deleted_in_objects(self):
        """The default queryset used by Playlist.objects contains no deleted playlists."""
        self.assertEqual(models.Playlist.objects.filter(deleted_at__isnull=False).count(), 0)

    def test_deleted_in_objects_including_deleted(self):
        """If we explicitly ask for deleted objects, we get them."""
        self.assertGreater(
            models.Playlist.objects_including_deleted.filter(deleted_at__isnull=False).count(), 0)

    def test_public_playlist_viewable_by_anon(self):
        """The public playlist is viewable by anonymous."""
        self.assert_user_can_view(AnonymousUser(), 'public')

    def test_signedin_playlist_not_viewable_by_anon(self):
        """The signedin playlist is not viewable by anonymous."""
        self.assert_user_cannot_view(AnonymousUser(), 'signedin')

    def test_user_of_none_is_treated_as_anon(self):
        """
        If a user of "None" is passed to viewable_by_user(), it is treated as the anonymous user.
        """
        self.assert_user_can_view(None, 'public')
        self.assert_user_cannot_view(None, 'signedin')

    def test_public_playlist_viewable_by_signed_in(self):
        """The public playlist is viewable by a signed in user."""
        self.assert_user_can_view(self.user, 'public')

    def test_signedin_playlist_viewable_by_signed_in(self):
        """The signedin playlist is viewable by a signed in user."""
        self.assert_user_can_view(self.user, 'signedin')

    def test_playlist_with_no_perms_not_viewable(self):
        """A playlist with empty permissions is not viewable by the anonymous or signed in user."""
        self.assert_user_cannot_view(AnonymousUser(), 'emptyperm')
        self.assert_user_cannot_view(self.user, 'emptyperm')

    def test_playlist_with_matching_crsid_viewable(self):
        """
        A user who's crsid is in the set of crsids for a playlist can view it.

        """
        self.assert_user_can_view(self.user, 'crsidsperm')

    def test_playlist_with_matching_lookup_groups_viewable(self):
        """
        A user who has at least one lookup group which is in the set of lookup groups for a
        playlist can view it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = ['A', 'B', 'C'], []
        self.assert_user_can_view(self.user, 'groupsperm')

    def test_playlist_with_matching_lookup_insts_viewable(self):
        """
        A user who has at least one lookup institution which is in the set of lookup institutions
        for a playlist can view it.

        """
        self.lookup_groupids_and_instids_for_user.return_value = [], ['A', 'B', 'C']
        self.assert_user_can_view(self.user, 'instsperm')

    def test_view_permission_created(self):
        """A new Playlist has a view permission created on save()."""
        playlist = models.Playlist.objects.create(channel=self.channel1)
        self.assertIsNotNone(models.Playlist.objects.get(id=playlist.id).view_permission)

    def test_has_media_items(self):
        """A Playlist has media items."""
        playlist = models.Playlist.objects.get(id='public')
        media_items = models.MediaItem.objects.filter(
            id__in=playlist.media_items
        ).viewable_by_user(AnonymousUser())
        # 'signin' cannot be viewed by 'anon', 'deleted' is flagged deleted,
        # and 'notfound' doesn't exist
        self.assertEqual(media_items.count(), 1)
        # only 'public' can be viewed
        self.assertEqual(media_items.first().id, 'public')
