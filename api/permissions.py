from rest_framework import permissions


class IsShopkeeper(permissions.BasePermission):
    """Allows access only to authenticated users with the SHOPKEEPER role."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        role = getattr(user, 'role', None)
        if role is None and hasattr(user, 'notification_preferences'):
            # Fallback to role in notification_preferences
            role = user.notification_preferences.get('role')

        return role is not None and role.upper() == "SHOPKEEPER"


def check_object_owner(obj, user):
    """Helper function to check if user is the owner of an object."""
    if hasattr(obj, "owner"):
        return obj.owner == user
    if hasattr(obj, "user"):
        return obj.user == user
    return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allows only object owners to perform write operations."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return check_object_owner(obj, request.user)


class IsShopOwnerOrReadOnly(permissions.BasePermission):
    """Restricts write operations on objects linked to a shop to the shop owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            hasattr(obj, "shop") and
            hasattr(obj.shop, "owner") and
            obj.shop.owner == request.user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Limits write operations to admin (staff) users only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
