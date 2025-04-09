"""
Wagtail hooks for the CMS app.

These hooks customize the Wagtail admin interface and add functionality.
"""

import cloudinary
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
# Updated imports for Wagtail v6
from wagtail_modeladmin.options import (ModelAdmin, ModelAdminGroup,
                                        modeladmin_register)

from apps.categories.models import Category
from apps.cms.admin import ApiModelAdmin
from apps.deals.models import Deal
from apps.products.models import Product
from apps.search.models import ScraperJob
from apps.shops.models import Shop


class ShopOwnerMixin:
    """Mixin to filter content by shop owner."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff:
            return qs
        return qs.filter(owner=request.user)


class ShopAdmin(ShopOwnerMixin, ApiModelAdmin):
    """Admin interface for the Shop model."""

    model = Shop
    menu_label = "Shops"
    menu_icon = "home"
    list_display = (
        "name",
        "owner",
        "is_verified",
        "sustainability_score",
        "created_at",
        "website",
    )
    list_filter = ("is_verified", "sustainability_score")
    search_fields = ("name", "description", "short_description")
    inspect_view_enabled = True
    inspect_view_fields = [
        "id",
        "name",
        "description",
        "website",
        "owner",
        "location",
        "rating",
        "sustainability_score",
        "created_at",
        "updated_at",
    ]


class ProductAdmin(ShopOwnerMixin, ApiModelAdmin):
    """Admin interface for products."""

    model = Product
    menu_label = "Products"
    menu_icon = "tag"
    list_display = (
        "name",
        "shop",
        "price_display",
        "stock_display",
        "is_available",
        "sustainability_score",
    )
    list_filter = ("is_available", "is_featured", "shop")
    search_fields = ("name", "description", "sku", "barcode")
    inspect_view_enabled = True
    inspect_view_fields = [
        "id",
        "name",
        "description",
        "price",
        "shop",
        "sustainability_score",
        "created_at",
        "updated_at",
    ]

    def price_display(self, obj):
        """Display price with discount if available."""
        if obj.discount_percentage > 0:
            return format_html(
                '<span style="text-decoration: line-through">${}</span> '
                '<span style="color: green; font-weight: bold">${}</span> '
                '<span style="background-color: #FFEB3B; padding: 2px 5px; border-radius: 3px">{}% OFF</span>',
                obj.price,
                obj.discounted_price,
                obj.discount_percentage,
            )
        return f"${obj.price}"

    price_display.short_description = "Price"
    price_display.admin_order_field = "price"

    def stock_display(self, obj):
        """Display stock with color-coding based on level."""
        if obj.stock_quantity <= 0:
            return format_html(
                '<span style="color: red; font-weight: bold">Out of stock</span>'
            )
        elif obj.stock_quantity < 10:
            return format_html(
                '<span style="color: orange; font-weight: bold">Low: {}</span>',
                obj.stock_quantity,
            )
        else:
            return format_html(
                '<span style="color: green">{}</span>', obj.stock_quantity
            )

    stock_display.short_description = "Stock"
    stock_display.admin_order_field = "stock_quantity"


class DealAdmin(ShopOwnerMixin, ApiModelAdmin):
    """Admin interface for deals."""

    model = Deal
    menu_label = "Deals"
    menu_icon = "pick"
    list_display = ("title", "shop", "discount_percentage", "end_date", "is_verified")
    list_filter = ("is_verified", "is_featured", "sustainability_score")
    search_fields = ("title", "description")
    inspect_view_enabled = True
    inspect_view_fields = [
        "id",
        "title",
        "description",
        "shop",
        "original_price",
        "discounted_price",
        "discount_percentage",
        "start_date",
        "end_date",
        "sustainability_score",
    ]


class CategoryAdmin(ApiModelAdmin):
    """Admin interface for categories."""

    model = Category
    menu_label = "Categories"
    menu_icon = "folder-open-inverse"
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inspect_view_enabled = True
    inspect_view_fields = ["id", "name", "description", "parent", "is_active"]


class ScraperJobAdmin(ApiModelAdmin):
    """Admin interface for scraper jobs."""

    model = ScraperJob
    menu_label = "Scraper Jobs"
    menu_icon = "code"
    list_display = (
        "job_type",
        "status",
        "created_at",
        "completed_at",
        "sustainability_score",
    )
    list_filter = ("status", "job_type")

    def has_permission(self, request):
        return request.user.is_staff


class DealopiaAdminGroup(ModelAdminGroup):
    menu_label = "Dealopia API"
    menu_icon = "folder-open-inverse"
    menu_order = 200
    items = (ShopAdmin, ProductAdmin, DealAdmin, CategoryAdmin, ScraperJobAdmin)


modeladmin_register(DealopiaAdminGroup)


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """Insert custom CSS in the Wagtail admin."""
    return format_html('<link rel="stylesheet" href="{}">', static("css/admin.css"))


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """Insert custom JavaScript in the Wagtail admin."""
    return format_html('<script src="{}"></script>', static("js/admin.js"))


@hooks.register("register_admin_menu_item")
def register_dashboard_menu_item():
    """Add a custom dashboard menu item to the Wagtail admin."""
    return MenuItem(
        "API Dashboard",
        reverse("admin:index") + "api/",
        classnames="icon icon-cog",
        order=10000,
    )


@hooks.register("construct_main_menu")
def hide_explorer_menu_item(request, menu_items):
    """Hide the 'Explorer' menu item since we're not using pages."""
    menu_items[:] = [item for item in menu_items if item.name != "explorer"]


@hooks.register("before_edit_page")
def set_default_transformation_options(request, page):
    """
    Set default transformation options for any images added to pages.
    """
    pass


@hooks.register("after_create_image")
def optimize_new_image(image):
    """
    Apply optimizations to newly uploaded images.
    """
    if hasattr(image, "transformation_options") and not image.transformation_options:
        image.transformation_options = {
            "quality": "auto",
            "fetch_format": "auto",
            "responsive": True,
            "width": "auto",
            "dpr": "auto",
            "crop": "limit",
        }
        image.save()
