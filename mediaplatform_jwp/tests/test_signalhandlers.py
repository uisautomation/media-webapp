from unittest import mock

from django.test import TestCase, override_settings

import mediaplatform.models as mpmodels

from .. import signalhandlers


class SyncItemsTestCase(TestCase):
    def test_setting(self):
        """The JWP_SYNC_ITEMS setting is respected."""
        with override_settings(JWP_SYNC_ITEMS=False):
            self.assertFalse(signalhandlers._should_sync_items())
        with override_settings(JWP_SYNC_ITEMS=True):
            self.assertTrue(signalhandlers._should_sync_items())

    def test_context_manager(self):
        """The JWP_SYNC_ITEMS setting can be overridden by the context manager."""
        with override_settings(JWP_SYNC_ITEMS=False):
            self.assertFalse(signalhandlers._should_sync_items())
            with signalhandlers.setting_sync_items(True):
                self.assertTrue(signalhandlers._should_sync_items())
            self.assertFalse(signalhandlers._should_sync_items())
        with override_settings(JWP_SYNC_ITEMS=True):
            self.assertTrue(signalhandlers._should_sync_items())
            with signalhandlers.setting_sync_items(False):
                self.assertFalse(signalhandlers._should_sync_items())
            self.assertTrue(signalhandlers._should_sync_items())

    def test_context_manager_nesting(self):
        """
        The JWP_SYNC_ITEMS setting can be overridden by the context manager which preserves
        the previous value if nested.

        """
        with override_settings(JWP_SYNC_ITEMS=False):
            self.assertFalse(signalhandlers._should_sync_items())
            with signalhandlers.setting_sync_items(True):
                self.assertTrue(signalhandlers._should_sync_items())
                with signalhandlers.setting_sync_items(False):
                    self.assertFalse(signalhandlers._should_sync_items())
                self.assertTrue(signalhandlers._should_sync_items())
            self.assertFalse(signalhandlers._should_sync_items())


@override_settings(JWP_SYNC_ITEMS=True)
class MediaItemSyncTestCase(TestCase):
    fixtures = ['mediaplatform_jwp/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        # Mock the item update function.
        self.schedule_item_update_patcher = mock.patch(
            'mediaplatform_jwp.management.schedule_item_update')
        self.schedule_item_update = self.schedule_item_update_patcher.start()
        self.addCleanup(self.schedule_item_update_patcher.stop)

    def test_basic_functionality(self):
        """
        Modifying a media item should synchronise the change with JWP.

        """
        i1 = mpmodels.MediaItem.objects.get(id='empty')
        i1.title = 'foo'
        i1.save()
        self.schedule_item_update.assert_called_once()
        self.assertEqual(self.schedule_item_update.call_args[0][0].id, i1.id)
        self.assertEqual(self.schedule_item_update.call_args[0][0].title, i1.title)

    def test_view_permission(self):
        """
        Modifying a media item's view permisson should synchronise the change with JWP.

        """
        i1 = mpmodels.MediaItem.objects.get(id='empty')
        i1.view_permission.crsids.append('spqr1')
        i1.view_permission.save()
        self.schedule_item_update.assert_called_once()
        self.assertEqual(self.schedule_item_update.call_args[0][0].id, i1.id)
        self.assertIn('spqr1', self.schedule_item_update.call_args[0][0].view_permission.crsids)

    def test_not_called_if_sync_disabled(self):
        """
        Disabling synchronsiation should not call schedule_item_update.

        """
        i1 = mpmodels.MediaItem.objects.get(id='empty')
        i1.title = 'foo'
        i1.view_permission.crsids.append('spqr1')
        with signalhandlers.setting_sync_items(False):
            i1.save()
            i1.view_permission.save()
        self.schedule_item_update.assert_not_called()
