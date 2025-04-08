from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.v1.serializers.deals import DealSerializer
from api.v1.serializers.shops import ShopCreateSerializer, ShopSerializer
from apps.shops.models import Shop


class ShopViewSet(viewsets.ModelViewSet):
    """ViewSet for Shop model with filtering, searching, and custom actions."""

    queryset = Shop.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ShopSerializer
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
        if self.action == "create":
            return ShopCreateSerializer
        return ShopSerializer

    @action(detail=False)
    def featured(self, request):
        featured_shops = Shop.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_shops, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def deals(self, request, pk=None):
        shop = self.get_object()
        deals = shop.deals.all().select_related("shop").prefetch_related("categories")
        serializer = DealSerializer(deals, many=True)
        return Response(serializer.data)
