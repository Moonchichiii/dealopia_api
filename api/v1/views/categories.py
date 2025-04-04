from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import IsAdminOrReadOnly
from api.v1.serializers.categories import CategorySerializer
from api.v1.serializers.deals import DealSerializer
from apps.categories.models import Category


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["parent", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "name"]
    ordering = ["order"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("children")

    @action(detail=True)
    def deals(self, request, pk=None):
        """Return deals associated with the specified category"""
        from apps.deals.services import DealService

        try:
            limit = self._get_limit_param(request, default=12)
            deals = DealService.get_deals_by_category(pk, limit)
            serializer = DealSerializer(deals, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid limit parameter"}, status=400)

    @action(detail=False)
    def featured(self, request):
        """Return popular categories that have active deals"""
        from apps.categories.services import CategoryService

        try:
            limit = self._get_limit_param(request, default=6)
            categories = CategoryService.get_popular_categories(limit)
            serializer = self.get_serializer(categories, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid limit parameter"}, status=400)

    def _get_limit_param(self, request, default=10):
        """Extract and validate the limit parameter from request"""
        limit = request.query_params.get("limit", default)
        return int(limit)

    @staticmethod
    def get_categories_by_name(name: str):
        return Category.objects.filter(name__icontains=name)
