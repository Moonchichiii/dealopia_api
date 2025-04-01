from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from decimal import Decimal

from api.v1.serializers.products import ProductSerializer, ProductListSerializer, ProductBulkUpdateSerializer
from apps.products.models import Product
from apps.products.services import ProductService
from api.permissions import IsShopOwnerOrReadOnly


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the Product model with advanced filtering, searching,
    and custom actions for product management.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsShopOwnerOrReadOnly]
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
        """Return appropriate serializer class based on action"""
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        """
        Return queryset with appropriate prefetches and filters
        """
        queryset = Product.objects.all().select_related('shop').prefetch_related('categories')
        
        # Apply custom filtering based on query parameters
        params = self.request.query_params
        
        # Filter by price range
        min_price = params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by stock availability
        in_stock = params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock_quantity__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock_quantity=0)
        
        # Filter by discount (has discount)
        has_discount = params.get('has_discount')
        if has_discount is not None and has_discount.lower() == 'true':
            queryset = queryset.filter(discount_percentage__gt=0)
        
        return queryset
        
    def perform_create(self, serializer):
        """
        Create a new product, enforcing shop ownership
        """
        # If user is not a staff member, they can only create products for shops they own
        user = self.request.user
        shop_id = serializer.validated_data.get('shop').id
        
        if not user.is_staff and not user.shops.filter(id=shop_id).exists():
            self.permission_denied(
                self.request,
                message="You can only create products for shops you own."
            )
        
        serializer.save()
        
    @action(detail=True, methods=['patch'])
    def update_stock(self, request, pk=None):
        """Update product stock quantity"""
        product = self.get_object()
        new_quantity = request.data.get('stock_quantity')
        
        if new_quantity is None:
            return Response(
                {"error": "stock_quantity is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_quantity = int(new_quantity)
            if new_quantity < 0:
                raise ValueError("Stock quantity cannot be negative")
                
            updated_product = ProductService.update_product_stock(product.id, new_quantity)
            serializer = self.get_serializer(updated_product)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """Increment product view count"""
        product = self.get_object()
        updated_product = ProductService.increment_view_count(product.id)
        
        return Response({
            "product_id": updated_product.id,
            "view_count": updated_product.view_count
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        shop_id = request.query_params.get('shop')
        
        if shop_id:
            products = ProductService.get_featured_products(shop_id=shop_id)
        else:
            products = ProductService.get_featured_products()
            
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_discounts(self, request):
        """Get products with discounts"""
        min_discount = request.query_params.get('min_discount', 10)
        products = ProductService.get_products_with_discounts(min_discount=min_discount)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related products based on shared categories"""
        limit = int(request.query_params.get('limit', 5))
        products = ProductService.get_related_products(pk, limit=limit)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update_prices(self, request):
        """
        Bulk update prices for products in a shop and/or category
        """
        serializer = ProductBulkUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        shop_id = data.get('shop_id')
        category_id = data.get('category_id')
        price_change_percentage = data.get('price_change_percentage')
        operation = data.get('operation', 'increase')
        
        # Validate shop ownership
        user = request.user
        if not user.is_staff and not user.shops.filter(id=shop_id).exists():
            return Response(
                {"error": "You can only update products for shops you own"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Query products to update
        products = Product.objects.filter(shop_id=shop_id)
        if category_id:
            products = products.filter(categories__id=category_id)
        
        # Calculate new prices
        updated_count = 0
        for product in products:
            if operation == 'increase':
                factor = Decimal('1') + (Decimal(price_change_percentage) / Decimal('100'))
            else:  # decrease
                factor = Decimal('1') - (Decimal(price_change_percentage) / Decimal('100'))
                
            new_price = round(product.price * factor, 2)
            product.price = new_price
            product.save(update_fields=['price', 'updated_at'])
            updated_count += 1
            
        return Response({
            "updated_count": updated_count,
            "operation": operation,
            "percentage": price_change_percentage
        })
        
    @action(detail=False, methods=['post'])
    def bulk_update_availability(self, request):
        """
        Bulk update product availability
        """
        shop_id = request.data.get('shop_id')
        product_ids = request.data.get('product_ids', [])
        is_available = request.data.get('is_available')
        
        if shop_id is None or is_available is None:
            return Response(
                {"error": "shop_id and is_available are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate shop ownership
        user = request.user
        if not user.is_staff and not user.shops.filter(id=shop_id).exists():
            return Response(
                {"error": "You can only update products for shops you own"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Query products to update
        products = Product.objects.filter(shop_id=shop_id)
        if product_ids:
            products = products.filter(id__in=product_ids)
            
        updated_count = products.update(is_available=is_available)
        
        return Response({
            "updated_count": updated_count,
            "is_available": is_available
        })