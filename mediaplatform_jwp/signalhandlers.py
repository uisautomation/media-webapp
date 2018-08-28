"""
Register and handle signals for the jwplatform integration application. This module is import-ed
from :py:class:`mediaplatform_jwp.apps.Config.ready` so all models should be registered at import
time.

"""
import contextlib
import threading

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from mediaplatform import models as mpmodels

from . import managementapi as management


_CONTEXT = threading.local()


@contextlib.contextmanager
def setting_sync_items(sync_items):
    """
    Context manager which can be used to override the behaviour controlled by the JWP_SYNC_ITEMS
    setting within the context. Takes a single argument which is the effective value of the setting
    within the context.

    """
    had_previous_value = hasattr(_CONTEXT, 'sync_items')
    if had_previous_value:
        previous_value = _CONTEXT.sync_items

    _CONTEXT.sync_items = sync_items

    yield

    if had_previous_value:
        _CONTEXT.sync_items = previous_value
    else:
        del _CONTEXT.sync_items


@receiver(post_save, sender=mpmodels.MediaItem)
def media_item_post_save_handler(*args, instance, raw, **kwargs):
    """
    Called when after a :py:class:`mediaplatform.models.MediaItem.save` method is called.
    If JWP_SYNC_ITEMS is set then modifications to media items are propagated to the corresponding
    JWP video (if any).

    """
    # If this is a "raw" object create (e.g. part of a test fixture), do not schedule any tasks.
    if raw or not _should_sync_items():
        return

    management.schedule_item_update(instance)


@receiver(post_save, sender=mpmodels.Permission)
def permission_post_save_handler(*args, instance, raw, **kwargs):
    """
    Called when after a :py:class:`mediaplatform.models.Permission.save` method is called.
    If JWP_SYNC_ITEMS is set then modifications to media items are propagated to the corresponding
    JWP video (if any).

    """
    # If this is a "raw" object create (e.g. part of a test fixture), do not schedule any tasks.
    if raw or not _should_sync_items():
        return

    if instance.allows_view_item is not None:
        management.schedule_item_update(instance.allows_view_item)


def _should_sync_items():
    """
    Return a boolean indicating if JWP videos should be synchronised to changes in media items.

    """
    return getattr(_CONTEXT, 'sync_items', settings.JWP_SYNC_ITEMS)
