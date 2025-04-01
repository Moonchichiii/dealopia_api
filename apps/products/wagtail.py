from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.modeladmin.helpers import ButtonHelper, PermissionHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from wagtail.contrib.modeladmin.views import IndexView

from apps.shops.wagtail import ShopOwnerMixin
from .models import Product


class ProductAdmin(ShopOwnerMixin, ModelAdmin):
    """Admin interface for managing products."""
    model = Product
    menu_label = 'Products'
    menu_icon = 'package'
    menu_order = 100
    list_display = (
        'name', 'shop', 'price_display', 'stock_display', 
        'is_available', 'is_featured'
    )
    list_filter = ('is_available', 'is_featured', 'shop')
    search_fields = ('name', 'description', 'sku', 'barcode')
    
    panels = [
        MultiFieldPanel([
            FieldPanel('shop'),
            FieldPanel('name'),
            FieldPanel('description'),
            FieldPanel('categories', widget='forms.CheckboxSelectMultiple'),
        ], heading='Basic Information'),
        MultiFieldPanel([
            FieldPanel('price'),
            FieldPanel('discount_percentage'),
            FieldPanel('stock_quantity'),
            FieldPanel('sku'),
            FieldPanel('barcode'),
            FieldPanel('is_available'),
            FieldPanel('is_featured'),
        ], heading='Product Details'),
        MultiFieldPanel([
            FieldPanel('image'),
            FieldPanel('additional_images'),
        ], heading='Images'),
        MultiFieldPanel([
            FieldPanel('weight'),
            FieldPanel('weight_unit'),
            FieldPanel('dimensions'),
        ], heading='Physical Attributes'),
        MultiFieldPanel([
            FieldPanel('specifications'),
            FieldPanel('meta_title'),
            FieldPanel('meta_description'),
        ], heading='Additional Information'),
        MultiFieldPanel([
            FieldPanel('view_count', read_only=True),
            FieldPanel('purchase_count', read_only=True),
        ], heading='Analytics', classname='collapsed'),
    ]
    
    def price_display(self, obj):
        """Display price with discount if available."""
        if obj.discount_percentage > 0:
            return format_html(
                '<span style="text-decoration: line-through">${}</span> '
                '<span style="color: green; font-weight: bold">${}</span> '
                '<span style="background-color: #FFEB3B; padding: 2px 5px; '
                'border-radius: 3px">{}% OFF</span>',
                obj.price, obj.discounted_price, obj.discount_percentage
            )
        return f'${obj.price}'
    
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def stock_display(self, obj):
        """Display stock with color-coding based on level."""
        if obj.stock_quantity <= 0:
            return format_html(
                '<span style="color: red; font-weight: bold">'
                'Out of stock</span>'
            )
        elif obj.stock_quantity < 10:
            return format_html(
                '<span style="color: orange; font-weight: bold">'
                'Low: {}</span>', 
                obj.stock_quantity
            )
        else:
            return format_html(
                '<span style="color: green">{}</span>', 
                obj.stock_quantity
            )
    
    stock_display.short_description = 'Stock'
    stock_display.admin_order_field = 'stock_quantity'
    
    def get_queryset(self, request):
        """Filter products to only show those for shops owned by the user."""
        qs = super().get_queryset(request)
        
        if request.user.is_staff:
            return qs
        
        # Shop owners can only see products for their shops
        return qs.filter(shop__owner=request.user)
    
    def get_form_fields_exclude(self, request):
        """Exclude certain fields based on user permissions."""
        excluded = super().get_form_fields_exclude(request) or []
        
        # Regular shop owners shouldn't be able to modify analytics
        if not request.user.is_staff:
            excluded.extend(['view_count', 'purchase_count'])
            
        return excluded
        
    def save_model(self, request, obj, form, change):
        """Ensure shop owner can only create products for their own shops."""
        if not request.user.is_staff:
            # Check if user owns the shop
            if obj.shop.owner != request.user:
                raise PermissionDenied(
                    "You can only create products for shops you own."
                )
                
        return super().save_model(request, obj, form, change)


class ProductButtonHelper(ButtonHelper):
    """Custom button helper to add bulk action buttons."""
    
    def update_stock_button(self, pk):
        """Return a button to update stock."""
        return {
            'url': self.url_helper.get_action_url('update_stock', pk),
            'label': 'Update Stock',
            'classname': 'button button-small',
            'title': 'Update stock for this product',
        }
        
    def bulk_discount_button(self):
        """Return a button for bulk discount action."""
        return {
            'url': self.url_helper.get_action_url('bulk_discount'),
            'label': 'Bulk Discount',
            'classname': 'button button-small button-secondary',
            'title': 'Apply discount to multiple products',
        }
        
    def get_buttons_for_obj(self, obj, *args, **kwargs):
        """Add custom buttons to the list of buttons."""
        buttons = super().get_buttons_for_obj(obj, *args, **kwargs)
        
        # Add update stock button
        buttons.append(self.update_stock_button(obj.pk))
        
        return buttons


class ProductPermissionHelper(PermissionHelper):
    """Custom permission helper for product actions."""
    
    def user_can_update_stock(self, user, obj):
        """Check if user can update stock."""
        # Staff can always update stock
        if user.is_staff:
            return True
            
        # Shop owners can update stock for their own products
        if obj and obj.shop.owner == user:
            return True
            
        return False
        
    def user_can_bulk_discount(self, user):
        """Check if user can apply bulk discounts."""
        # Staff can always apply bulk discounts
        if user.is_staff:
            return True
            
        # Shop owners can apply bulk discounts to their own products
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
        """Add bulk action buttons to the header."""
        buttons = super().get_header_buttons(request)
        
        # Add bulk discount button if user has permission
        ph = self.permission_helper
        if ph.user_can_bulk_discount(request.user):
            buttons.append(self.button_helper.bulk_discount_button())
            
        return buttons


# Register with Wagtail's admin
modeladmin_register(ProductAdmin)