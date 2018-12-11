import datetime
from unittest import mock

from django.test import TestCase

from mediaplatform import models as mpmodels

from mediaplatform_jwp.api import management as management


class ItemSyncTestCase(TestCase):
    fixtures = ['mediaplatform_jwp/tests/fixtures/mediaitems.yaml']

    def setUp(self):
        self.no_jwp_item = mpmodels.MediaItem.objects.get(id='empty')
        self.jwp_item = mpmodels.MediaItem.objects.get(id='existing')

        # Patch JWP client
        self.get_jwp_client_patcher = (
            mock.patch('mediaplatform_jwp.api.delivery.get_jwplatform_client'))
        self.get_jwp_client = self.get_jwp_client_patcher.start()
        self.addCleanup(self.get_jwp_client_patcher.stop)
        self.jwp_client = self.get_jwp_client()

        self.jwp_client.videos.create.return_value = {'media': {'key': 'newvideo'}}
        self.jwp_client.videos.update.return_value = {}
        self.existing_tags = ['one', 'two']
        self.jwp_client.videos.show.return_value = {
            'video': {'key': 'existingvideo', 'tags': ','.join(self.existing_tags)},
        }

    def test_create_if_necessary(self):
        management._perform_item_update(self.no_jwp_item)
        self.jwp_client.videos.create.assert_called_once()

    def test_raises_error_if_odd_response_from_create(self):
        self.jwp_client.videos.create.return_value = {}
        with self.assertRaises(RuntimeError):
            management._perform_item_update(self.no_jwp_item)

    def test_no_create_if_not_necessary(self):
        management._perform_item_update(self.jwp_item)
        self.jwp_client.videos.create.assert_not_called()

    def test_title_sync(self):
        self.jwp_item.title = 'xxxx'
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, title=self.jwp_item.title)

    def test_description_sync(self):
        self.jwp_item.description = 'xxxx'
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, description=self.jwp_item.description)

    def test_published_at_sync(self):
        self.jwp_item.published_at = datetime.datetime(
            year=2013, month=12, day=11, hour=10, minute=9, second=8)
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(
            self.jwp_item.jwp.key, date=int(self.jwp_item.published_at.timestamp()))

    def test_downloadable_sync(self):
        self.jwp_item.downloadable = True
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_downloadable': 'downloadable:{}:'.format(repr(self.jwp_item.downloadable))
        })

    def test_language_sync(self):
        self.jwp_item.language = 'eng'
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_language': 'language:{}:'.format(self.jwp_item.language)
        })

    def test_copyright_sync(self):
        self.jwp_item.copyright = 'eng'
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_copyright': 'copyright:{}:'.format(self.jwp_item.copyright)
        })

    def test_keywords_sync(self):
        self.jwp_item.tags = ['aaa', 'bbb']
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_keywords': 'keywords:{}:'.format('|'.join(self.jwp_item.tags))
        })

    def test_view_permission_public_sync(self):
        self.jwp_item.view_permission.reset()
        self.jwp_item.view_permission.is_public = True
        self.jwp_item.view_permission.save()
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_acl': 'acl:WORLD:'
        })

    def test_view_permission_signed_in_sync(self):
        self.jwp_item.view_permission.reset()
        self.jwp_item.view_permission.is_signed_in = True
        self.jwp_item.view_permission.save()
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_acl': 'acl:CAM:'
        })

    def test_view_permission_crsid_sync(self):
        self.jwp_item.view_permission.reset()
        self.jwp_item.view_permission.crsids = ['spqr1']
        self.jwp_item.view_permission.save()
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_acl': 'acl:USER_spqr1:'
        })

    def test_view_permission_group_sync(self):
        self.jwp_item.view_permission.reset()
        self.jwp_item.view_permission.lookup_groups = ['01234']
        self.jwp_item.view_permission.save()
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_acl': 'acl:GROUP_01234:'
        })

    def test_view_permission_inst_sync(self):
        self.jwp_item.view_permission.reset()
        self.jwp_item.view_permission.lookup_insts = ['BOTOLPH']
        self.jwp_item.view_permission.save()
        management._perform_item_update(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, **{
            'custom.sms_acl': 'acl:INST_BOTOLPH:'
        })

    def test_records_upload_links(self):
        """If update response includes link data, it is recorded."""
        link_data = {'protocol': 'http'}
        self.jwp_client.videos.update.return_value.update({'link': link_data})
        with mock.patch('mediaplatform_jwp.upload.record_link_response') as rlr_mock:
            management._perform_item_update(self.jwp_item)
            rlr_mock.assert_called_once_with(link_data, self.jwp_item)

    def test_create_upload_endpoint(self):
        link_data = {'protocol': 'http'}
        self.jwp_client.videos.update.return_value.update({'link': link_data})
        with mock.patch('mediaplatform_jwp.upload.record_link_response') as rlr_mock:
            management.create_upload_endpoint(self.jwp_item)
        self.assert_video_updated(self.jwp_item.jwp.key, update_file=True)
        rlr_mock.assert_called_once_with(link_data, self.jwp_item)

    def test_create_upload_endpoint_requires_jwp_video(self):
        with self.assertRaises(ValueError):
            management.create_upload_endpoint(self.no_jwp_item)

    def test_site_tags_and_props_created(self):
        """A new video has media id custom props set and sitedomain tag"""
        management._perform_item_update(self.no_jwp_item)
        self.jwp_client.videos.create.assert_called_once()
        _, kwargs = self.jwp_client.videos.create.call_args
        self.assertIn('tags', kwargs)

        # A site tag should be created
        site_tags = [t for t in kwargs['tags'].split(',') if t.startswith('sitedomain:')]
        self.assertEqual(len(site_tags), 1)
        _, site = site_tags[0].split(':')

        # Custom props for the site should include media id
        self.assertIn('custom.site.' + site.replace('.', '_') + '.name', kwargs)
        self.assertIn('custom.site.' + site.replace('.', '_') + '.media_id', kwargs)
        self.assertEqual(
            kwargs['custom.site.' + site.replace('.', '_') + '.media_id'],
            self.no_jwp_item.id)

    def test_site_tags_and_props_added(self):
        """
        An existing video has media id custom props set and sitedomain tag set but existing
        tags preserved.

        """
        management._perform_item_update(self.jwp_item)
        self.jwp_client.videos.update.assert_called_once()
        _, kwargs = self.jwp_client.videos.update.call_args
        self.assertIn('tags', kwargs)
        all_tags = kwargs['tags'].split(',')

        # All existing tags should be preserved
        for t in self.existing_tags:
            self.assertIn(t, all_tags)

        # A site tag should be created
        site_tags = [t for t in all_tags if t.startswith('sitedomain:')]
        self.assertEqual(len(site_tags), 1)
        _, site = site_tags[0].split(':')

        # Custom props for the site should include media id
        self.assertIn('custom.site.' + site.replace('.', '_') + '.name', kwargs)
        self.assertIn('custom.site.' + site.replace('.', '_') + '.media_id', kwargs)
        self.assertEqual(
            kwargs['custom.site.' + site.replace('.', '_') + '.media_id'],
            self.jwp_item.id)

    def assert_video_updated(self, key, **kwargs):
        self.jwp_client.videos.update.assert_called_once()
        called_kwargs = self.jwp_client.videos.update.call_args[1]
        self.assertEqual(called_kwargs['video_key'], key)
        for k, v in kwargs.items():
            self.assertIn(k, called_kwargs)
            self.assertEqual(called_kwargs[k], v)
