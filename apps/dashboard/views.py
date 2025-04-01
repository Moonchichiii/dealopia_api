from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, F, Q
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail.admin.views.home import HomeView

from apps.shops.models import Shop
from apps.products.models import Product
from apps.deals.models import Deal


class ShopOwnerDashboardView(LoginRequiredMixin, TemplateView):
    """Custom dashboard for shop owners in Wagtail."""
    template_name = 'dashboard/shop_owner_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Redirect to shop creation page if user has no shops.
        Allow staff to access regardless of shop ownership.
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if (not hasattr(request.user, 'shops') or 
                not request.user.shops.exists()):
            if not request.user.is_staff:
                return redirect('wagtailadmin_explore_root')
                
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Provide context data for the dashboard including shop statistics,
        products, and deals information.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        shops = user.shops.all() if not user.is_staff else Shop.objects.all()
        context['shops'] = shops
        
        if shops.exists():
            shop = shops.first()
            context['shop'] = shop
            
            today = timezone.now().date()
            thirty_days_ago = today - timezone.timedelta(days=30)
            
            context['total_products'] = Product.objects.filter(
                shop=shop).count()
            context['active_products'] = Product.objects.filter(
                shop=shop, is_available=True).count()
            
            active_deals = Deal.objects.filter(
                shop=shop,
                is_verified=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            context['active_deals'] = active_deals
            context['active_deals_count'] = active_deals.count()
            
            context['low_stock_products'] = Product.objects.filter(
                shop=shop,
                is_available=True,
                stock_quantity__lt=10
            ).order_by('stock_quantity')[:5]
            
            context['top_viewed_products'] = Product.objects.filter(
                shop=shop
            ).order_by('-view_count')[:5]
            
            context['top_purchased_products'] = Product.objects.filter(
                shop=shop
            ).order_by('-purchase_count')[:5]
            
            context['recent_products'] = Product.objects.filter(
                shop=shop
            ).order_by('-created_at')[:5]
            
            categories = shop.categories.all()
            category_stats = []
            
            for category in categories:
                products_count = Product.objects.filter(
                    shop=shop,
                    categories=category
                ).count()
                
                if products_count > 0:
                    category_stats.append({
                        'name': category.name,
                        'products_count': products_count
                    })
            
            context['category_stats'] = category_stats
            
        return context


@hooks.register('register_admin_urls')
def register_dashboard_url():
    """Register the shop owner dashboard URL."""
    return [
        path('shop-dashboard/', 
             ShopOwnerDashboardView.as_view(), 
             name='shop_owner_dashboard'),
    ]


@hooks.register('construct_main_menu')
def hide_pages_for_shop_owners(request, menu_items):
    """Hide menu items not relevant to shop owners."""
    user = request.user
    
    if not user.is_staff and hasattr(user, 'shops') and user.shops.exists():
        allowed_menu_items = [
            'dashboard', 'shop-management', 'products', 
            'images', 'documents'
        ]
        menu_items[:] = [
            item for item in menu_items if item.name in allowed_menu_items
        ]


@hooks.register('construct_homepage_panels')
def add_shop_stats_panel(request, panels):
    """
    Redirect shop owners to custom dashboard, replacing default panels.
    """
    user = request.user
    
    if not user.is_staff and hasattr(user, 'shops') and user.shops.exists():
        return [
            Component({
                'request': request,
                'redirect_url': reverse('shop_owner_dashboard'),
            })
        ]
