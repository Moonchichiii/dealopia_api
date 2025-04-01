# apps/api/wagtail_api.py
from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.endpoints import ImagesAPIEndpoint
from wagtail.documents.api.v2.endpoints import DocumentsAPIEndpoint

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.shops.models import Shop
from apps.products.models import Product
from apps.deals.models import Deal
from apps.api.v1.serializers.shops import ShopSerializer, ShopListSerializer
from apps.api.v1.serializers.products import ProductSerializer, ProductListSerializer
from apps.api.v1.serializers.deals import DealSerializer, DealListSerializer

# Create the API router
api_router = WagtailAPIRouter('wagtailapi')

# Register the API endpoints
api_router.register_endpoint('pages', PagesAPIEndpoint)
api_router.register_endpoint('images', ImagesAPIEndpoint)
api_router.register_endpoint('documents', DocumentsAPIEndpoint)


# Enhanced Shop API with Wagtail integration
class ShopWagtailViewSet(viewsets.ModelViewSet):
    """ViewSet for Shop model with Wagtail CMS integration."""
    queryset = Shop.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["categories", "is_verified", "is_featured"]
    search_fields = ["name", "description", "short_description"]
    ordering_fields = ["created_at", "name", "rating"]
    ordering = ["-created_at"]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ShopListSerializer
        return ShopSerializer
    
    @action(detail=True)
    def cms_preview(self, request, pk=None):
        """Get preview data for shop CMS page."""
        shop = self.get_object()
        
        # Get shop data
        serializer = self.get_serializer(shop)
        shop_data = serializer.data
        
        # Get active deals
        from django.utils import timezone
        deals = Deal.objects.filter(
            shop=shop,
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by("-is_featured", "-created_at")[:5]
        deal_serializer = DealListSerializer(deals, many=True, context=self.context)
        
        # Get products
        products = Product.objects.filter(
            shop=shop,
            is_available=True
        ).order_by("-is_featured", "-created_at")[:6]
        product_serializer = ProductListSerializer(products, many=True, context=self.context)
        
        # Combine the data
        preview_data = {
            "shop": shop_data,
            "deals": deal_serializer.data,
            "products": product_serializer.data
        }
        
        return Response(preview_data)


# Enhanced Product API with Wagtail integration
class ProductWagtailViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model with Wagtail CMS integration."""
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'shop': ['exact'],
        'categories': ['exact'],
        'is_available': ['exact'],
        'is_featured': ['exact'],
        'price': ['gte', 'lte'],
        'discount_percentage': ['gte'],
    }
    search_fields = ['name', 'description', 'sku', 'barcode']
    ordering_fields = ['created_at', 'price', 'name', 'stock_quantity', 'view_count', 'purchase_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    @action(detail=True)
    def cms_preview(self, request, pk=None):
        """Get preview data for product CMS page."""
        product = self.get_object()
        
        # Get product data
        serializer = self.get_serializer(product)
        product_data = serializer.data
        
        # Increment view count
        from apps.products.services import ProductService
        ProductService.increment_view_count(product.id)
        
        # Get related products
        related_products = ProductService.get_related_products(product.id, limit=4)
        related_serializer = ProductListSerializer(related_products, many=True, context=self.context)
        
        # Get active deal if any
        best_deal = product.get_best_deal()
        deal_data = None
        if best_deal:
            deal_serializer = DealSerializer(best_deal, context=self.context)
            deal_data = deal_serializer.data
        
        # Combine the data
        preview_data = {
            "product": product_data,
            "related_products": related_serializer.data,
            "deal": deal_data
        }
        
        return Response(preview_data)


# API URLs configuration - add to your urls.py
"""
from django.urls import path, include
from .wagtail_api import api_router, ShopWagtailViewSet, ProductWagtailViewSet
from rest_framework.routers import DefaultRouter

# Create a router for the enhanced viewsets
router = DefaultRouter()
router.register(r'shops', ShopWagtailViewSet)
router.register(r'products', ProductWagtailViewSet)

urlpatterns = [
    # Wagtail API
    path('api/wagtail/', api_router.urls),
    
    # Enhanced API with CMS integration
    path('api/cms/', include(router.urls)),
]
"""