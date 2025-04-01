from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
)
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)

from .models import Shop, Review


class ShopOwnerMixin:
    """Mixin to filter content by shop owner."""
    
    def get_queryset(self, request):
        """Return queryset filtered by owner for non-staff users."""
        qs = super().get_queryset(request)
        
        # Staff sees everything
        if request.user.is_staff:
            return qs
            
        # Shop owners only see their own content
        return qs.filter(owner=request.user)
        
    def get_edit_handler(self):
        """Customize edit handler based on user permissions."""
        panels = super().get_edit_handler().children
        
        # For non-staff users, exclude certain fields
        if not self.request.user.is_staff:
            restricted_fields = ['is_verified', 'is_featured', 'rating']
            panels = [
                panel for panel in panels 
                if getattr(panel, 'field_name', None) not in restricted_fields
            ]
        
        return ObjectList(panels)


class ShopAdmin(ShopOwnerMixin, ModelAdmin):
    """Admin interface for Shop model."""
    model = Shop
    menu_label = 'Shops'
    menu_icon = 'store'
    menu_order = 100
    list_display = ('name', 'owner', 'is_verified', 'rating', 
                   'active_deals_count')
    list_filter = ('is_verified', 'is_featured')
    search_fields = ('name', 'description', 'short_description')
    form_fields_exclude = ['rating']
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('owner'),
            FieldPanel('description'),
            FieldPanel('short_description'),
            FieldPanel('logo'),
            FieldPanel('banner_image'),
        ], heading='Basic Information'),
        MultiFieldPanel([
            FieldPanel('website'),
            FieldPanel('phone'),
            FieldPanel('email'),
        ], heading='Contact Information'),
        MultiFieldPanel([
            FieldPanel('categories', widget='forms.CheckboxSelectMultiple'),
            FieldPanel('location'),
            FieldPanel('opening_hours'),
        ], heading='Shop Details'),
        MultiFieldPanel([
            FieldPanel('is_verified'),
            FieldPanel('is_featured'),
        ], heading='Admin Settings'),
        MultiFieldPanel([
            FieldPanel('carbon_neutral'),
            FieldPanel('sustainability_initiatives'),
            FieldPanel('verified_sustainable'),
        ], heading='Sustainability'),
    ]
    
    def active_deals_count(self, obj):
        """Display active deals count with link to deals."""
        count = obj.active_deals_count
        url = reverse('wagtailadmin_explore_root')
        return format_html('<a href="{}">{} active deals</a>', url, count)
    
    active_deals_count.short_description = 'Active Deals'
    
    def get_form_fields_exclude(self, request):
        """Exclude fields based on user permissions."""
        excluded = super().get_form_fields_exclude(request) or []
        
        if not request.user.is_staff:
            excluded.extend(['is_verified', 'is_featured', 'rating'])
            
        return excluded


class ReviewAdmin(ShopOwnerMixin, ModelAdmin):
    """Admin interface for Review model."""
    model = Review
    menu_label = 'Reviews'
    menu_icon = 'star'
    menu_order = 200
    list_display = ('__str__', 'shop', 'user', 'rating', 'is_approved', 
                   'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('comment', 'shop__name', 'user__email')
    
    panels = [
        FieldPanel('shop'),
        FieldPanel('user'),
        FieldPanel('rating'),
        FieldPanel('comment'),
        FieldPanel('is_approved'),
    ]
    
    def get_queryset(self, request):
        """Filter reviews to only show those for shops owned by the user."""
        qs = super().get_queryset(request)
        
        if request.user.is_staff:
            return qs
            
        # Shop owners can only see reviews for their shops
        return qs.filter(shop__owner=request.user)


class ShopGroup(ModelAdminGroup):
    """Group for shop-related admin interfaces."""
    menu_label = 'Shop Management'
    menu_icon = 'store'
    menu_order = 200
    items = (ShopAdmin, ReviewAdmin)


modeladmin_register(ShopGroup)
