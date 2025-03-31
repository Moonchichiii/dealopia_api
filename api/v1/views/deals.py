import re
from typing import List, Optional, Union

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from api.permissions import IsShopOwnerOrReadOnly
from api.v1.serializers.deals import DealDetailSerializer, DealSerializer
from apps.deals.models import Deal
from apps.deals.services import DealService


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsShopOwnerOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "shop": ["exact"],
        "categories": ["exact", "in"],
        "is_featured": ["exact"],
        "is_exclusive": ["exact"],
        "sustainability_score": ["gte", "lte"],
        "local_production": ["exact"],
    }
    search_fields = ["title", "description", "shop__name", "eco_certifications"]
    ordering_fields = [
        "created_at",
        "discount_percentage",
        "end_date",
        "views_count",
        "sustainability_score",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_staff:
            return queryset

        if self.request.user.is_authenticated:
            owned_shops = self.request.user.shops.all()
            if owned_shops.exists():
                return queryset.filter(shop__in=owned_shops)

        return Deal.get_active()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DealDetailSerializer
        return super().get_serializer_class()

    @extend_schema(
        parameters=[
            OpenApiParameter(name="category", description="Category ID"),
            OpenApiParameter(name="shop", description="Shop ID"),
            OpenApiParameter(name="limit", description="Result limit", type=int),
        ]
    )
    @action(detail=False)
    def featured(self, request):
        limit = self._parse_int_param(request.query_params.get("limit", 6))
        category = request.query_params.get("category")
        shop = request.query_params.get("shop")

        queryset = DealService.get_featured_deals(limit, category)

        if shop:
            queryset = [deal for deal in queryset if str(deal.shop_id) == shop]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="lat", description="Latitude", required=True, type=float
            ),
            OpenApiParameter(
                name="lng", description="Longitude", required=True, type=float
            ),
            OpenApiParameter(name="radius", description="Radius in km", type=float),
            OpenApiParameter(
                name="min_sustainability",
                description="Min sustainability score",
                type=float,
            ),
            OpenApiParameter(
                name="categories", description="Category IDs (comma-separated)"
            ),
            OpenApiParameter(name="limit", description="Result limit", type=int),
        ]
    )
    @action(detail=False)
    def nearby(self, request):
        try:
            lat = float(request.query_params.get("lat", ""))
            lng = float(request.query_params.get("lng", ""))
            radius = float(request.query_params.get("radius", 10))
            limit = self._parse_int_param(request.query_params.get("limit", 20))

            min_sustainability = self._parse_float_param(
                request.query_params.get("min_sustainability")
            )
            categories = self._parse_comma_separated_ints(
                request.query_params.get("categories")
            )

            deals = DealService.get_deals_near_location(
                lat, lng, radius, limit, min_sustainability, categories
            )

            serializer = self.get_serializer(deals, many=True)
            return Response(serializer.data)
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="min_score", description="Minimum sustainability score", type=float
            ),
            OpenApiParameter(name="limit", description="Result limit", type=int),
        ]
    )
    @action(detail=False)
    def sustainable(self, request):
        try:
            min_score = float(request.query_params.get("min_score", 7.0))
            limit = self._parse_int_param(request.query_params.get("limit", 10))

            deals = DealService.get_sustainable_deals(min_score, limit)
            serializer = self.get_serializer(deals, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def track_view(self, request, pk=None):
        DealService.record_interaction(pk, "view")
        return Response({"status": "view recorded"})

    @action(detail=True, methods=["post"])
    def track_click(self, request, pk=None):
        DealService.record_interaction(pk, "click")
        return Response({"status": "click recorded"})

    def _parse_int_param(self, value, default=None) -> int:
        if value is None and default is not None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default or 0

    def _parse_float_param(self, value) -> Optional[float]:
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_comma_separated_ints(self, value) -> Optional[List[int]]:
        if not value:
            return None
        try:
            return [int(item) for item in value.split(",")]
        except (ValueError, TypeError):
            return None
