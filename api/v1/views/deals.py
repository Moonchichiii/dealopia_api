# api/v1/views/deals.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.deals.models import Deal
from apps.deals.services import DealService
from api.v1.serializers.deals import DealSerializer, DealDetailSerializer
from api.permissions import IsShopOwnerOrReadOnly


class DealViewSet(viewsets.ModelViewSet):
    """
    API endpoint for deals management with advanced filtering and search capabilities.
    """
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsShopOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shop', 'categories', 'is_featured', 'is_exclusive']
    search_fields = ['title', 'description', 'shop__name']
    ordering_fields = ['created_at', 'discount_percentage', 'end_date', 'views_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only show active deals by default"""
        queryset = super().get_queryset()
        
        # Allow admin/staff to see all deals
        if self.request.user.is_staff:
            return queryset
            
        # For shop owners, show all their deals
        if self.request.user.is_authenticated:
            # Get deals from shops owned by the user
            owned_shops = self.request.user.shops.all()
            if owned_shops.exists():
                # Show both active and inactive deals for the owner's shops
                return queryset.filter(shop__in=owned_shops)
        
        # For regular users and anonymous, show only active deals
        return DealService.get_active_deals(queryset)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return DealDetailSerializer
        return super().get_serializer_class()
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='category', description='Filter by category ID'),
            OpenApiParameter(name='shop', description='Filter by shop ID'),
            OpenApiParameter(name='limit', description='Number of results to return')
        ]
    )
    @action(detail=False)
    def featured(self, request):
        """Get featured deals"""
        limit = int(request.query_params.get('limit', 6))
        category = request.query_params.get('category')
        shop = request.query_params.get('shop')
        
        queryset = DealService.get_featured_deals(limit)
        
        if category:
            queryset = queryset.filter(categories__id=category)
        if shop:
            queryset = queryset.filter(shop__id=shop)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='days', description='Days until expiration'),
            OpenApiParameter(name='limit', description='Number of results to return')
        ]
    )
    @action(detail=False)
    def ending_soon(self, request):
        """Get deals ending soon"""
        days = int(request.query_params.get('days', 3))
        limit = int(request.query_params.get('limit', 6))
        
        queryset = DealService.get_expiring_soon_deals(days, limit)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='lat', description='Latitude', required=True),
            OpenApiParameter(name='lng', description='Longitude', required=True),
            OpenApiParameter(name='radius', description='Radius in kilometers')
        ]
    )
    @action(detail=False)
    def nearby(self, request):
        """Find deals near a specified location"""
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Valid latitude and longitude are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        radius = float(request.query_params.get('radius', 10))
        queryset = DealService.get_deals_by_location(lat, lng, radius)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        """Track that a deal was viewed"""
        DealService.record_view(pk)
        return Response({"status": "view recorded"})
    
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track that a deal was clicked"""
        DealService.record_click(pk)
        return Response({"status": "click recorded"})
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Number of related deals to return')
        ]
    )
    @action(detail=True)
    def related(self, request, pk=None):
        """Get deals related to this one"""
        deal = self.get_object()
        limit = int(request.query_params.get('limit', 3))
        
        related_deals = DealService.get_related_deals(deal, limit)
        serializer = self.get_serializer(related_deals, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get the current user's favorite deals"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # This would require a UserFavorite model which we'll implement separately
        favorite_deals = Deal.objects.filter(favorites__user=request.user)
        serializer = self.get_serializer(favorite_deals, many=True)
        
        return Response(serializer.data)