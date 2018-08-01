from rest_framework import permissions

import mediaplatform.models as mpmodels


class ObjectNotAnnotated(RuntimeError):
    """
    The object passed to the permission requires the viewable or editable annotation. See
    :py:class:`mediaplatform.models.MediaItemQuerySet.annotate_viewable` and
    :py:class:`mediaplatform.models.MediaItemQuerySet.annotate_editable`.

    """


class MediaItemPermission(permissions.BasePermission):
    """
    A permission which allows a user access to "safe" HTTP methods if they have the view permission
    and *additionally* requires the edit permission for "unsafe" HTTP methods.

    The "additional" above implies that a user cannot modify a video if they cannot view it even if
    they have the edit permission.

    Come what may, a user can do *nothing* to a deleted video.

    Raises :py:exc:`~.ObjectNotAnnotated` if the object has not had the appropriate permission
    flags annotated via :py:class:`mediaplatform.models.MediaItemQuerySet.annotate_viewable` or
    :py:class:`mediaplatform.models.MediaItemQuerySet.annotate_editable`.

    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only signed in users have permissions to perform "unsafe" operations
        if not hasattr(request, 'user') or request.user is None or request.user.is_anonymous:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        return self.has_media_item_permission(
            request, obj, requires_view=True,
            requires_edit=request.method not in permissions.SAFE_METHODS)

    def has_media_item_permission(self, request, obj, requires_view, requires_edit):
        # Sanity check that the passed object is a MediaItem.
        assert isinstance(obj, mpmodels.MediaItem)

        if requires_view and not hasattr(obj, 'viewable'):
            raise ObjectNotAnnotated('Item should be annotated via annotate_viewable()')

        if requires_edit and not hasattr(obj, 'editable'):
            raise ObjectNotAnnotated('Item should be annotated via annotate_editable()')

        return (not requires_view or obj.viewable) and (not requires_edit or obj.editable)


class MediaItemEditPermission(MediaItemPermission):
    """
    Like :py:class:`~.MediaItemPermission` except that the edit permission must *always* be
    present.

    """
    def has_object_permission(self, request, view, obj):
        return self.has_media_item_permission(
            request, obj, requires_view=True, requires_edit=True)
