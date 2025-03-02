from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.categories.models import Category
from api.v1.serializers.categories import CategorySerializer
from api.v1.serializers.deals import DealSerializer
from api.permissions import IsAdminOrReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name']
    ordering = ['order']
    
    @action(detail=True)
    def deals(self, request, pk=None):
        category = self.get_object()
        deals = category.deals.all()
        serializer = DealSerializer(deals, many=True)
        return Response(serializer.data)
