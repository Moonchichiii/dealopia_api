from rest_framework import permissions


def check_object_owner(obj, user):
    """Helper function to check if user is the owner of an object."""
    if hasattr(obj, "owner"):
        return obj.owner == user
    elif hasattr(obj, "user"):
        return obj.user == user
    return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allows only object owners to perform write operations."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return check_object_owner(obj, request.user)


class IsShopOwnerOrReadOnly(permissions.BasePermission):
    """Restricts deal modifications to shop owners only."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            hasattr(obj, "shop")
            and hasattr(obj.shop, "owner")
            and obj.shop.owner == request.user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Limits write operations to admin users only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
