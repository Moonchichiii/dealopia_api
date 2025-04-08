"""
Admin configurations for the CMS app.

This module contains the Wagtail admin panel configurations for the CMS app.
Since this is a backend-only API, we focus on API-related functionality.
"""

from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Use wagtail_modeladmin (installed as "wagtail_modeladmin") rather than "wagtail.modeladmin"
from wagtail_modeladmin.options import ModelAdmin
from wagtail_modeladmin.helpers import ButtonHelper, PermissionHelper
from wagtail_modeladmin.views import IndexView


class ApiModelAdmin(ModelAdmin):
    """
    Base ModelAdmin class with API-focused customizations.
    
    This class extends ModelAdmin with features specifically
    designed for managing API content.
    """
    list_display = ('id', 'created_at', 'updated_at')

    def api_link_button(self, obj):
        """Return a button to view the API endpoint for this object."""
        return format_html(
            '<a href="/api/v1/{}/{}/" class="button button-small" target="_blank">View API</a>',
            self.model._meta.model_name, obj.id
        )
    api_link_button.short_description = _('API Endpoint')

    def get_list_display(self, request):
        """Append API link button to list display if applicable."""
        list_display = super().get_list_display(request)
        if hasattr(self.model, 'id'):
            if self.model._meta.model_name in ['shop', 'product', 'deal', 'category']:
                return list_display + ('api_link_button',)
        return list_display

    def get_queryset(self, request):
        """Return queryset filtered based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_staff:
            return qs
        if hasattr(self.model, 'owner'):
            return qs.filter(owner=request.user)
        elif hasattr(self.model, 'shop') and hasattr(self.model.shop.field.related_model, 'owner'):
            return qs.filter(shop__owner=request.user)
        return qs.none()

    def user_can_edit_obj(self, request, obj):
        """Return True if the user can edit the object."""
        if request.user.is_staff:
            return True
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        if hasattr(obj, 'shop') and hasattr(obj.shop, 'owner') and obj.shop.owner == request.user:
            return True
        return False

    def user_can_delete_obj(self, request, obj):
        """Return True if the user can delete the object."""
        return self.user_can_edit_obj(request, obj)

    def save_model(self, request, obj, form, change):
        """Ensure shop owners only create content for shops they own."""
        if not request.user.is_staff:
            if hasattr(obj, 'shop') and obj.shop is not None:
                if obj.shop.owner != request.user:
                    raise PermissionDenied("You can only create content for shops you own.")
            if not change and hasattr(obj, 'owner') and obj.owner is None:
                obj.owner = request.user
        return super().save_model(request, obj, form, change)
        

class ProductButtonHelper(ButtonHelper):
    """Custom button helper to add bulk action buttons."""

    def update_stock_button(self, pk):
        """Return a button to update stock."""
        return {
            "url": self.url_helper.get_action_url("update_stock", pk),
            "label": "Update Stock",
            "classname": "button button-small",
            "title": "Update stock for this product",
        }

    def bulk_discount_button(self):
        """Return a button for bulk discount action."""
        return {
            "url": self.url_helper.get_action_url("bulk_discount"),
            "label": "Bulk Discount",
            "classname": "button button-small button-secondary",
            "title": "Apply discount to multiple products",
        }

    def get_buttons_for_obj(self, obj, *args, **kwargs):
        """Return the list of buttons for the given object."""
        buttons = super().get_buttons_for_obj(obj, *args, **kwargs)
        buttons.append(self.update_stock_button(obj.pk))
        return buttons


class ProductPermissionHelper(PermissionHelper):
    """Custom permission helper for product actions."""

    def user_can_update_stock(self, user, obj):
        """Return True if the user can update stock for the object."""
        if user.is_staff:
            return True
        if obj and obj.shop.owner == user:
            return True
        return False

    def user_can_bulk_discount(self, user):
        """Return True if the user can apply bulk discounts."""
        if user.is_staff:
            return True
        if user.shops.exists():
            return True
        return False


class ProductIndexView(IndexView):
    """Custom index view to add bulk action buttons."""

    def get_buttons_helper_class(self):
        """Return the custom button helper class."""
        return ProductButtonHelper

    def get_permission_helper_class(self):
        """Return the custom permission helper class."""
        return ProductPermissionHelper

    def get_header_buttons(self, request):
        """Return header buttons including bulk discount if permitted."""
        buttons = super().get_header_buttons(request)
        if self.permission_helper.user_can_bulk_discount(request.user):
            buttons.append(self.button_helper.bulk_discount_button())
        return buttons
