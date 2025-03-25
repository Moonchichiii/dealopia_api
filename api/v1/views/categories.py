from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.categories.models import Category
from api.permissions import IsAdminOrReadOnly
from api.v1.serializers.categories import CategorySerializer
from api.v1.serializers.deals import DealSerializer
from django_filters.rest_framework import DjangoFilterBackend


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name']
    ordering = ['order']
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related('children')
    
    @action(detail=True)
    def deals(self, request, pk=None):
        """Get deals for this category"""
        from apps.deals.services import DealService
        
        limit = int(request.query_params.get('limit', 12))
        deals = DealService.get_deals_by_category(pk, limit)
        
        serializer = DealSerializer(deals, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def featured(self, request):
        """Get featured categories with active deals"""
        from apps.categories.services import CategoryService
        
        limit = int(request.query_params.get('limit', 6))
        categories = CategoryService.get_popular_categories(limit)
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
