from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsShopOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission for deals to only allow shop owners to edit them."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if hasattr(obj, 'shop') and hasattr(obj.shop, 'owner'):
            return obj.shop.owner == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow admins to edit, but anyone to view."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)