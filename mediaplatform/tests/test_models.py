from django.test import TestCase

from .. import models


class MediaItemTest(TestCase):
    fixtures = ['mediaplatform/tests/fixtures/test_data.yaml']

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


class CollectionTest(TestCase):
    def test_creation(self):
        """A Collection object should be creatable with no field values."""
        models.Collection.objects.create()


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
