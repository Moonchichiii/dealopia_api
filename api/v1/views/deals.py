from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.deals.models import Deal
from api.v1.serializers.deals import DealSerializer
from api.permissions import IsShopOwnerOrReadOnly

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsShopOwnerOrReadOnly]  # Apply the permission
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shop', 'categories', 'is_featured', 'is_exclusive']
    search_fields = ['title', 'description', 'shop__name']
    ordering_fields = ['created_at', 'discount_percentage', 'end_date']
    ordering = ['-created_at']
    
    # Your existing action methods will inherit this permission
    # Featured and ending_soon are read-only actions, so anyone can access them
    # track_view and track_click will require the user to be the shop owner
