import datetime
import secrets

from django.utils import timezone
from django.test import TestCase
import pytz

import mediaplatform.models as mpmodels
import mediaplatform_jwp.models as jwpmodels
import legacysms.models as legacymodels
import mediaplatform_jwp.api.delivery as jwp
from .. models import set_resources, CachedResource

from .. import sync


class SyncTestCase(TestCase):
    def test_basic_functionality(self):
        """If a new video appears on JWP, a new MediaItem will be created to match it."""
        self.assertEqual(mpmodels.MediaItem.objects.count(), 0)
        video = make_video(media_id='1234', title='test title')
        set_resources_and_sync([video])
        self.assertEqual(mpmodels.MediaItem.objects.count(), 1)
        item = mpmodels.MediaItem.objects.get(jwp__key=video.key)
        self.assertEqual(item.title, 'test title')

    def test_video_delete(self):
        """If a video is deleted, its media item is marked as deleted."""
        v1, v2 = make_video(media_id='1234'), make_video(media_id='2345')
        set_resources_and_sync([v1, v2])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        i2 = mpmodels.MediaItem.objects.get(jwp__key=v2.key)
        set_resources_and_sync([v1])
        self.assertIsNone(mpmodels.MediaItem.objects.get(id=i1.id).deleted_at)
        self.assertIsNotNone(mpmodels.MediaItem.objects_including_deleted.get(id=i2.id).deleted_at)
        self.assertFalse(mpmodels.MediaItem.objects.filter(id=i2.id).exists())

    def test_video_update(self):
        """If a video is updated, its corresponding media item is updated."""
        updated = timezone.now()
        v1 = make_video(media_id='1234', updated=updated)
        v2 = make_video(media_id='5678', updated=updated)
        set_resources_and_sync([v1, v2])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        i2 = mpmodels.MediaItem.objects.get(jwp__key=v2.key)

        # Update video 1 but not 2
        v1['updated'] += 1
        v1['title'] += 'new title'
        set_resources_and_sync([v1, v2])

        new_i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        new_i2 = mpmodels.MediaItem.objects.get(jwp__key=v2.key)

        # Only video 1 was updated
        self.assertGreater(new_i1.updated_at, i1.updated_at)
        self.assertEqual(new_i1.title, v1['title'])
        self.assertEqual(new_i2.updated_at, i2.updated_at)

    def test_sync_jwp(self):
        """New videos should create matching JWP video objects."""
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        jwp1 = jwpmodels.Video.objects.get(key=v1.key)
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertIsNotNone(i1.jwp)
        self.assertEqual(jwp1.key, v1.key)

    def test_update_jwp(self):
        """A video update should be reflected in the JWP video object."""
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        jwp1 = jwpmodels.Video.objects.get(key=v1.key)
        self.assertEqual(jwp1.updated, v1['updated'])

        v1['updated'] += 20
        v1, = set_resources_and_sync([v1])
        jwp1 = jwpmodels.Video.objects.get(key=v1.key)
        self.assertEqual(jwp1.updated, v1['updated'])

    def test_default_sync(self):
        """
        Check the default synchronised values.

        """
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertEqual(i1.downloadable, False)
        self.assertEqual(i1.language, '')
        self.assertEqual(i1.copyright, '')
        self.assertEqual(i1.tags, [])
        self.assertTrue(hasattr(i1, 'sms'))

    def test_sync_title(self):
        self.assert_attribute_sync('title')

    def test_sync_description(self):
        self.assert_attribute_sync('description')

    def test_sync_date(self):
        self.assert_attribute_sync(
            'date',
            model_attr='published_at',
            test_value=utc_timestamp_to_datetime(123456))

    def test_sync_duration(self):
        self.assert_attribute_sync('duration', test_value=10.2)
        # missing duration is handled
        v1, = set_resources_and_sync([make_video(media_id='1234', duration=None)])
        self.assertEqual(0., mpmodels.MediaItem.objects.get(jwp__key=v1.key).duration)

    def test_sync_type(self):
        self.assert_attribute_sync('mediatype', model_attr='type', test_value='unknown')

    def test_sync_downloadable(self):
        self.assert_attribute_sync('downloadable', test_value=True)
        self.assert_attribute_sync('downloadable', test_value=False)

    def test_sync_language(self):
        self.assert_attribute_sync('language', test_value='eng')

    def test_sync_copyright(self):
        self.assert_attribute_sync('copyright', test_value='Some dude, I guess')

    def test_sync_tags(self):
        self.assert_attribute_sync(
            'keywords', model_attr='tags', test_value=['kw1', 'kw2 with spaces'])

    def test_sync_sms_media_id(self):
        v1, = set_resources_and_sync([make_video(media_id='12345')])
        self.assertEqual(
            12345, mpmodels.MediaItem.objects.get(jwp__key=v1.key).sms.id)

    def test_update_deleted_item(self):
        """A deleted media item should not be touched by update."""
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        set_resources_and_sync([])
        self.assertIsNotNone(mpmodels.MediaItem.objects_including_deleted.get(id=i1.id).deleted_at)
        self.assertFalse(mpmodels.MediaItem.objects.filter(id=i1.id).exists())
        self.assertFalse(
            hasattr(mpmodels.MediaItem.objects_including_deleted.get(id=i1.id), 'jwp'))
        i1_v2 = mpmodels.MediaItem.objects_including_deleted.get(id=i1.id)
        set_resources_and_sync([], update_kwargs={'update_all_videos': True})
        self.assertEqual(
            i1_v2.updated_at,
            mpmodels.MediaItem.objects_including_deleted.get(id=i1.id).updated_at)

    def test_basic_acl(self):
        """A video with no ACL maps to a Permission which denies everything."""
        v1, = set_resources_and_sync([make_video(acl=[], media_id='1234')])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)

        self.assertEqual(i1.view_permission.crsids, [])
        self.assertEqual(i1.view_permission.lookup_groups, [])
        self.assertEqual(i1.view_permission.lookup_insts, [])
        self.assertFalse(i1.view_permission.is_public)
        self.assertFalse(i1.view_permission.is_signed_in)

    def test_view_acls(self):
        """A video with ACLs maps to view permission."""
        v1, v2, v3 = set_resources_and_sync([
            make_video(
                media_id='123', acl=['USER_spqr1', 'USER_abcd1', 'INST_botolph', 'GROUP_1234']),
            make_video(media_id='456', acl=['WORLD']),
            make_video(media_id='789', acl=['CAM']),
        ])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        i2 = mpmodels.MediaItem.objects.get(jwp__key=v2.key)
        i3 = mpmodels.MediaItem.objects.get(jwp__key=v3.key)

        self.assertEqual(i1.view_permission.crsids, ['spqr1', 'abcd1'])
        self.assertEqual(i1.view_permission.lookup_groups, ['1234'])
        self.assertEqual(i1.view_permission.lookup_insts, ['botolph'])
        self.assertFalse(i1.view_permission.is_public)
        self.assertFalse(i1.view_permission.is_signed_in)

        self.assertEqual(i2.view_permission.crsids, [])
        self.assertEqual(i2.view_permission.lookup_groups, [])
        self.assertEqual(i2.view_permission.lookup_insts, [])
        self.assertTrue(i2.view_permission.is_public)
        self.assertFalse(i2.view_permission.is_signed_in)

        self.assertEqual(i3.view_permission.crsids, [])
        self.assertEqual(i3.view_permission.lookup_groups, [])
        self.assertEqual(i3.view_permission.lookup_insts, [])
        self.assertFalse(i3.view_permission.is_public)
        self.assertTrue(i3.view_permission.is_signed_in)

    def test_item_update_with_sms(self):
        """Test that updating an item's SMS last_updated_at updates SMS item."""
        last_updated_at = timezone.now()
        v1, = set_resources_and_sync([
            make_video(media_id='1234', last_updated_at=last_updated_at)
        ])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertEqual(i1.sms.last_updated_at, last_updated_at)

        # Simulate a SMS update
        v1['updated'] += 20
        new_last_updated_at = timezone.now() + datetime.timedelta(seconds=20)
        v1['custom']['sms_last_updated_at'] = 'last_updated_at:{}:'.format(
            new_last_updated_at.isoformat()
        )

        set_resources_and_sync([v1])
        i1_v2 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertEqual(i1_v2.sms.last_updated_at, new_last_updated_at)

    def test_item_update_with_sms_going_away(self):
        """Test that an SMS media item going away deletes it from the DB."""
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertEqual(i1.sms.id, 1234)

        # Simulate a SMS delete
        del v1['custom']['sms_media_id']
        v1['updated'] += 1
        set_resources_and_sync([v1])

        # SMS object should've been deleted
        i1_v2 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)
        self.assertFalse(hasattr(i1_v2, 'sms'))
        self.assertEqual(legacymodels.MediaItem.objects.filter(id=1234).count(), 0)

    def test_item_update_with_modifiying_cached_resource(self):
        """
        A change up the updated field in the Cached resource should re-sync the video.

        """
        v1, = set_resources_and_sync([make_video(media_id='1234')])
        i1 = mpmodels.MediaItem.objects.get(jwp__key=v1.key)

        resource = CachedResource.videos.get(key=v1.key)
        new_title = i1.title + '-changed'
        resource.data['title'] = new_title
        resource.data['updated'] += 1
        resource.save()

        sync.update_related_models_from_cache()

        self.assertEqual(mpmodels.MediaItem.objects.get(jwp__key=v1.key).title, new_title)

    def test_basic_channel_functionality(self):
        """If a new video and channel appears on JWP, objects are created."""
        self.assertEqual(mpmodels.MediaItem.objects.count(), 0)
        set_resources_and_sync(
            [make_video(title='test title', media_id='1')],
            [make_channel(
                title='test channel', media_ids=['1'], collection_id='2',
                instid='UIS',
            )],
        )
        self.assertEqual(mpmodels.MediaItem.objects.count(), 1)
        c = mpmodels.Channel.objects.filter(sms__id='2').first()
        self.assertIsNotNone(c)
        self.assertEqual(len(c.items.all()), 1)
        self.assertEqual(c.items.all()[0].title, 'test title')
        self.assertEqual(c.billing_account.lookup_instid, 'UIS')

    def test_basic_playlist_functionality(self):
        """If a new video and channel appears on JWP, objects are created."""
        self.assertEqual(mpmodels.MediaItem.objects.count(), 0)
        set_resources_and_sync(
            [make_video(title='test title', media_id='1')],
            [make_channel(
                title='Didius Julianus',
                description='What evil have I done?',
                media_ids=['1'],
                collection_id='2',
                instid='UIS',
            )],
        )
        media_item = mpmodels.MediaItem.objects.first()
        playlist = mpmodels.Playlist.objects.filter(sms__id='2').first()

        self.assertEqual(playlist.title, 'Didius Julianus')
        self.assertEqual(playlist.description, 'What evil have I done?')
        self.assertEqual(len(playlist.media_items), 1)
        self.assertEqual(playlist.media_items[0], media_item.id)

    def test_adding_media_to_channel(self):
        """If a new video and channel appears on JWP, objects are created."""
        videos = [
            make_video(title='test title', media_id='1'),
            make_video(title='test title 2', media_id='2'),
        ]
        channels = [make_channel(title='test channel', media_ids=['1'], collection_id='3')]
        set_resources_and_sync(videos, channels)
        c = mpmodels.Channel.objects.filter(sms__id='3').first()
        self.assertIsNotNone(c)
        self.assertEqual(len(c.items.all()), 1)
        channels[0]['custom']['sms_media_ids'] = 'media_ids:1,2:'
        channels[0]['updated'] += 1
        set_resources_and_sync(videos, channels)
        self.assertEqual(len(c.items.all()), 2)
        # also check playlist
        playlist = mpmodels.Playlist.objects.filter(sms__id='3').first()
        self.assertEqual(len(playlist.media_items), 2)

    def test_edit_acls(self):
        videos = [
            make_video(title='test title 1', media_id='1'),
            make_video(title='test title 2', media_id='2'),
        ]
        channels = [
            make_channel(title='test channel 1', media_ids=['1'], collection_id='3',
                         groupid='01234'),
            make_channel(title='test channel 2', media_ids=['2'], collection_id='4'),
        ]

        channels[0]['custom']['sms_created_by'] = 'created_by:spqr1:'
        channels[1]['custom']['sms_created_by'] = 'creator:abcd1:'

        set_resources_and_sync(videos, channels)

        c1 = mpmodels.Channel.objects.filter(sms__id='3').first()
        c2 = mpmodels.Channel.objects.filter(sms__id='4').first()
        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)

        self.assertIn('spqr1', c1.edit_permission.crsids)
        self.assertNotIn('abcd1', c1.edit_permission.crsids)
        self.assertNotIn('spqr1', c2.edit_permission.crsids)
        self.assertIn('abcd1', c2.edit_permission.crsids)
        self.assertIn('01234', c1.edit_permission.lookup_groups)
        self.assertNotIn('01234', c2.edit_permission.lookup_groups)

    def test_last_updated_sync(self):
        """If a new video and channel appears on JWP, objects are created."""
        last_updated_at = timezone.now()
        videos = [
            make_video(title='test title', media_id='1'),
        ]
        channels = [
            make_channel(title='test channel', media_ids=['1'], collection_id='2',
                         last_updated_at=last_updated_at)
        ]
        set_resources_and_sync(videos, channels)
        c = mpmodels.Channel.objects.filter(sms__id=2).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.sms.last_updated_at, last_updated_at)

    def test_channel_update_with_sms_going_away(self):
        """Test that an SMS channel going away deletes it from the DB."""
        videos = [
            make_video(title='test title', media_id='1'),
        ]
        channels = [
            make_channel(title='test channel', media_ids=['1'], collection_id='2')
        ]
        set_resources_and_sync(videos, channels)
        c1 = mpmodels.Channel.objects.get(jwp__key=channels[0].key)
        self.assertEqual(c1.sms.id, 2)
        self.assertEqual(legacymodels.Collection.objects.filter(id=2).count(), 1)

        # check the Playlist has SMS object
        playlist = mpmodels.Playlist.objects.filter(sms__id='2').first()
        self.assertTrue(hasattr(playlist, 'sms'))

        # Simulate a SMS delete
        del channels[0]['custom']['sms_collection_id']
        channels[0]['updated'] += 1
        set_resources_and_sync(videos, channels)

        # SMS object should've been deleted
        c1_v2 = mpmodels.Channel.objects.get(jwp__key=channels[0].key)
        self.assertFalse(hasattr(c1_v2, 'sms'))
        self.assertEqual(legacymodels.Collection.objects.filter(id=2).count(), 0)

        # check the Playlist doesn't have SMS object
        playlist = mpmodels.Playlist.objects.get(id=playlist.id)
        self.assertFalse(hasattr(playlist, 'sms'))

    def test_only_sms_created(self):
        """Only videos with SMS media ids are autocreated."""
        v1, v2 = make_video(media_id='1234'), make_video()
        set_resources_and_sync([v1, v2])
        i1 = mpmodels.MediaItem.objects.filter(jwp__key=v1.key).first()
        self.assertIsNotNone(i1)
        i2 = mpmodels.MediaItem.objects.filter(jwp__key=v2.key).first()
        self.assertIsNone(i2)

    def test_recreate_deleted_item(self):
        """If a media item is deleted but not the cached resource or JWP video, the item is
        re-created and synched."""
        v1 = make_video(media_id='1234', title='testing')
        set_resources_and_sync([v1])
        i1 = mpmodels.MediaItem.objects.filter(jwp__key=v1.key).first()
        self.assertIsNotNone(i1)
        self.assertEqual(i1.title, 'testing')
        i1.delete()

        set_resources_and_sync([v1])
        i1 = mpmodels.MediaItem.objects.filter(jwp__key=v1.key).first()
        self.assertIsNotNone(i1)
        self.assertEqual(i1.title, 'testing')

    def assert_attribute_sync(self, video_attr, model_attr=None, test_value='testing'):
        """
        Assert that an attribute on the video dict is correctly transferred to the underlying
        model.

        """
        model_attr = model_attr if model_attr is not None else video_attr
        v1, = set_resources_and_sync([make_video(**{'media_id': '1234', video_attr: test_value})])
        self.assertEqual(
            test_value, getattr(mpmodels.MediaItem.objects.get(jwp__key=v1.key), model_attr))


def set_resources_and_sync(videos, channels=[], update_kwargs={}):
    """
    Convenience wrapper which sets the cached video resource and synchronises the DB. Returns its
    argument.

    """
    set_resources(videos, 'video')
    set_resources(channels, 'channel')
    sync.update_related_models_from_cache(**update_kwargs)
    return videos


def make_video(**kwargs):
    """
    Create a new video resource fixture. The following keyword arguments are supported:

    * key - default, return value of secrets.token_urlsafe()
    * title - default ""
    * description - default ""
    * date - publication datetime, defaults to now()
    * updated - updated datetime, defaults to now()
    * duration - duration in seconds, defaults to 123.45
    * mediatype - one of {'video', 'audio', 'unknown'}, defaults to 'unknown'
    * downloadable - maps to custom.sms_downloadable. defaults to not being present
    * keywords - list of str, maps to custom.sms_keywords. defaults to not being present
    * media_id - SMS media id, maps to custom.sms_media_id. defaults to not being present
    * copyright - maps to custom.sms_copyright. defaults to not being present
    * language - maps to custom.sms_language. defaults to not being present
    * acl - list of str. maps to custom.sms_acl. defaults to not being present
    * created_by - CRSid of creator. maps to custom.sms_created_by defaults to not being present
    * last_updated_at - last update datetime on SMS. maps to custom.sms_last_updated_at
        defaults to not being present

    """

    custom = {}

    if 'downloadable' in kwargs:
        custom['sms_downloadable'] = 'downloadable:{}:'.format(kwargs['downloadable'])

    if 'keywords' in kwargs:
        custom['sms_keywords'] = 'keywords:{}:'.format('|'.join(kwargs['keywords']))

    if 'media_id' in kwargs:
        custom['sms_media_id'] = 'media:{}:'.format(kwargs['media_id'])

    if 'copyright' in kwargs:
        custom['sms_copyright'] = 'copyright:{}:'.format(kwargs['copyright'])

    if 'language' in kwargs:
        custom['sms_language'] = 'language:{}:'.format(kwargs['language'])

    if 'acl' in kwargs:
        custom['sms_acl'] = 'acl:{}:'.format(','.join(kwargs['acl']))

    if 'created_by' in kwargs:
        custom['sms_created_by'] = 'created_by:{}:'.format(kwargs['created_by'])

    if 'last_updated_at' in kwargs:
        custom['sms_last_updated_at'] = 'last_updated_at:{}:'.format(
            kwargs['last_updated_at'].isoformat())

    video = {
        'key': kwargs.get('key', secrets.token_urlsafe()),
        'title': kwargs.get('title', ''),
        'description': kwargs.get('description', ''),
        'date': int(kwargs.get('date', timezone.now()).timestamp()),
        'updated': int(kwargs.get('updated', timezone.now()).timestamp()),
        'duration': kwargs.get('duration', 123.45),
        'mediatype': kwargs.get('mediatype', 'unknown'),
    }

    if len(custom) > 0:
        video['custom'] = custom

    return jwp.Video(video)


def make_channel(**kwargs):
    """
    Create a new channel resource fixture. The following keyword arguments are supported:

    * key - default, return value of secrets.token_urlsafe()
    * title - default ""
    * description - default ""
    * collection_id - maps to custom.sms_collection_id. defaults to not being present
    * instid - maps to custom.sms_instid. defaults to not being present
    * groupid - maps to custom.sms_groupid. defaults to not being present
    * updated - updated datetime, defaults to now()
    * media_ids - SMS media ids, maps to custom.sms_media_ids. defaults to not being present
    * acl - list of str. maps to custom.sms_acl. defaults to not being present
    * created_by - CRSid of creator. maps to custom.sms_created_by defaults to not being present
    * last_updated_at - last update datetime on SMS. maps to custom.sms_last_updated_at
        defaults to not being present

    """

    custom = {}

    if 'media_ids' in kwargs:
        custom['sms_media_ids'] = 'media_ids:{}:'.format(','.join(kwargs['media_ids']))

    if 'acl' in kwargs:
        custom['sms_acl'] = 'acl:{}:'.format(','.join(kwargs['acl']))

    if 'created_by' in kwargs:
        custom['sms_created_by'] = 'created_by:{}:'.format(kwargs['created_by'])

    if 'last_updated_at' in kwargs:
        custom['sms_last_updated_at'] = 'last_updated_at:{}:'.format(
            kwargs['last_updated_at'].isoformat())

    if 'instid' in kwargs:
        custom['sms_instid'] = 'instid:{}:'.format(kwargs['instid'])

    if 'groupid' in kwargs:
        custom['sms_groupid'] = 'groupid:{}:'.format(kwargs['groupid'])

    if 'collection_id' in kwargs:
        custom['sms_collection_id'] = 'collection:{}:'.format(kwargs['collection_id'])

    channel = {
        'key': kwargs.get('key', secrets.token_urlsafe()),
        'title': kwargs.get('title', ''),
        'description': kwargs.get('description', ''),
        'updated': int(kwargs.get('updated', timezone.now()).timestamp()),
    }

    if len(custom) > 0:
        channel['custom'] = custom

    return jwp.Channel(channel)


def utc_timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc)
