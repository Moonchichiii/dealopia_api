from django.urls import path, reverse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from wagtail import hooks
from wagtail.admin.ui.components import Component

from apps.deals.models import Deal
from apps.products.models import Product
from apps.shops.models import Shop


class ShopOwnerDashboardView(APIView):
    """
    API endpoint for shop owner dashboard statistics.

    Returns JSON data for use by your Vite/TypeScript frontend.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        if not hasattr(user, "shops") or not user.shops.exists():
            if not user.is_staff:
                return Response({"detail": "No shops found for this user."}, status=404)

        shops = user.shops.all() if not user.is_staff else Shop.objects.all()
        dashboard_data = {"shops": [shop.id for shop in shops]}

        if shops.exists():
            shop = shops.first()
            dashboard_data["shop"] = shop.id
            dashboard_data["total_products"] = Product.objects.filter(shop=shop).count()
            dashboard_data["active_products"] = Product.objects.filter(shop=shop, is_available=True).count()

            active_deals = Deal.objects.filter(
                shop=shop,
                is_verified=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            dashboard_data["active_deals_count"] = active_deals.count()

            dashboard_data["low_stock_products"] = list(
                Product.objects.filter(shop=shop, is_available=True, stock_quantity__lt=10)
                .order_by("stock_quantity")
                .values_list("id", flat=True)[:5]
            )
            dashboard_data["top_viewed_products"] = list(
                Product.objects.filter(shop=shop).order_by("-view_count").values_list("id", flat=True)[:5]
            )
            dashboard_data["top_purchased_products"] = list(
                Product.objects.filter(shop=shop).order_by("-purchase_count").values_list("id", flat=True)[:5]
            )
            dashboard_data["recent_products"] = list(
                Product.objects.filter(shop=shop).order_by("-created_at").values_list("id", flat=True)[:5]
            )

            category_stats = []
            for category in shop.categories.all():
                products_count = Product.objects.filter(shop=shop, categories=category).count()
                if products_count > 0:
                    category_stats.append({
                        "name": category.name,
                        "products_count": products_count,
                    })
            dashboard_data["category_stats"] = category_stats

        return Response(dashboard_data)


@hooks.register("register_admin_urls")
def register_dashboard_url():
    """Register the shop owner dashboard URL in the admin."""
    return [
        path("shop-dashboard/", ShopOwnerDashboardView.as_view(), name="shop_owner_dashboard"),
    ]


@hooks.register("construct_main_menu")
def hide_pages_for_shop_owners(request, menu_items):
    """Hide menu items not relevant to shop owners."""
    user = request.user
    if not user.is_staff and hasattr(user, "shops") and user.shops.exists():
        allowed_menu_items = ["dashboard", "shop-management", "products", "images", "documents"]
        menu_items[:] = [item for item in menu_items if item.name in allowed_menu_items]


@hooks.register("construct_homepage_panels")
def add_shop_stats_panel(request, panels):
    """Add a panel redirecting shop owners to the dashboard endpoint."""
    user = request.user
    if not user.is_staff and hasattr(user, "shops") and user.shops.exists():
        return [
            Component({
                "request": request,
                "redirect_url": reverse("shop_owner_dashboard"),
            })
        ]
