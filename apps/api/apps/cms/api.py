"""
Wagtail API configuration for the CMS app.

This file centralizes all Wagtail API endpoints and routers.
"""

from django.urls import path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
# Updated imports for Wagtail 6
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet

from api.v1.serializers.deals import DealListSerializer, DealSerializer
from api.v1.serializers.products import (ProductListSerializer,
                                         ProductSerializer)
from api.v1.serializers.shops import ShopListSerializer, ShopSerializer
from apps.deals.models import Deal
from apps.products.models import Product
from apps.shops.models import Shop

# Create the API router with a namespace
api_router = WagtailAPIRouter("wagtailapi")


# Register endpoints
api_router.register_endpoint("pages", PagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)


class ShopWagtailViewSet(viewsets.ModelViewSet):
    """ViewSet for Shop model with Wagtail CMS integration."""

    queryset = Shop.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["categories", "is_verified", "is_featured"]
    search_fields = ["name", "description", "short_description"]
    ordering_fields = ["created_at", "name", "rating"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ShopListSerializer
        return ShopSerializer

    @action(detail=True)
    def cms_preview(self, request, pk=None):
        """Return preview data for the shop CMS page."""
        shop = self.get_object()
        serializer = self.get_serializer(shop)
        shop_data = serializer.data

        from django.utils import timezone

        deals = Deal.objects.filter(
            shop=shop,
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        ).order_by("-is_featured", "-created_at")[:5]
        deal_serializer = DealListSerializer(
            deals, many=True, context=self.get_serializer_context()
        )

        products = Product.objects.filter(shop=shop, is_available=True).order_by(
            "-is_featured", "-created_at"
        )[:6]
        product_serializer = ProductListSerializer(
            products, many=True, context=self.get_serializer_context()
        )

        preview_data = {
            "shop": shop_data,
            "deals": deal_serializer.data,
            "products": product_serializer.data,
        }
        return Response(preview_data)


class ProductWagtailViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model with Wagtail CMS integration."""

    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "shop": ["exact"],
        "categories": ["exact"],
        "is_available": ["exact"],
        "is_featured": ["exact"],
        "price": ["gte", "lte"],
        "discount_percentage": ["gte"],
    }
    search_fields = ["name", "description", "sku", "barcode"]
    ordering_fields = [
        "created_at",
        "price",
        "name",
        "stock_quantity",
        "view_count",
        "purchase_count",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    @action(detail=True)
    def cms_preview(self, request, pk=None):
        """Return preview data for the product CMS page."""
        product = self.get_object()
        serializer = self.get_serializer(product)
        product_data = serializer.data

        from apps.products.services import ProductService

        ProductService.increment_view_count(product.id)
        related_products = ProductService.get_related_products(product.id, limit=4)
        related_serializer = ProductListSerializer(
            related_products, many=True, context=self.get_serializer_context()
        )

        best_deal = product.get_best_deal()
        deal_data = None
        if best_deal:
            deal_serializer = DealSerializer(
                best_deal, context=self.get_serializer_context()
            )
            deal_data = deal_serializer.data

        preview_data = {
            "product": product_data,
            "related_products": related_serializer.data,
            "deal": deal_data,
        }
        return Response(preview_data)
