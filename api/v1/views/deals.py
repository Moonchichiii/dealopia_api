import logging

from django.contrib.gis.geos import Point
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import IsShopOwnerOrReadOnly
from api.v1.serializers.deals import DealDetailSerializer, DealSerializer
from apps.deals.models import Deal
from apps.deals.services import DealService

logger = logging.getLogger(__name__)


class DealViewSet(viewsets.ModelViewSet):
    """API endpoint for deals with text search and geospatial filtering."""

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
    search_fields = [
        "title",
        "description",
        "shop__name",
        "eco_certifications",
        "categories__name",
    ]
    ordering_fields = [
        "created_at",
        "discount_percentage",
        "end_date",
        "views_count",
        "sustainability_score",
    ]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        """Filter deals by location and sustainability score if coordinates provided."""
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        min_score = float(request.query_params.get("min_score", 5.0))
        if latitude and longitude:
            queryset = DealService.get_local_and_sustainable_deals(
                float(latitude), float(longitude), radius_km=100, min_score=min_score
            )
        else:
            queryset = DealService.get_active_deals().filter(
                sustainability_score__gte=min_score
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        """Return featured deals with optional filtering."""
        limit = int(request.query_params.get("limit", 6))
        category = request.query_params.get("category")
        shop = request.query_params.get("shop")
        queryset = DealService.get_active_deals().filter(is_featured=True)
        if category:
            queryset = queryset.filter(categories__id=category)
        if shop:
            queryset = queryset.filter(shop=shop)
        queryset = queryset.order_by("-created_at")[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        """Return deals meeting minimum sustainability criteria."""
        try:
            min_score = float(request.query_params.get("min_score", 7.0))
            limit = int(request.query_params.get("limit", 10))
            deals = DealService.get_sustainable_deals(min_score, limit)
            serializer = self.get_serializer(deals, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def track_view(self, request, pk=None):
        """Record a view interaction for a deal."""
        DealService.record_interaction(pk, "view")
        return Response({"status": "view recorded"})

    @action(detail=True, methods=["post"])
    def track_click(self, request, pk=None):
        """Record a click interaction for a deal."""
        DealService.record_interaction(pk, "click")
        return Response({"status": "click recorded"})

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="latitude", description="User latitude", required=True, type=float
            ),
            OpenApiParameter(
                name="longitude",
                description="User longitude",
                required=True,
                type=float,
            ),
            OpenApiParameter(
                name="radius", description="Search radius in km", type=float, default=10
            ),
            OpenApiParameter(
                name="limit",
                description="Maximum number of results",
                type=int,
                default=20,
            ),
            OpenApiParameter(
                name="min_sustainability",
                description="Minimum sustainability score",
                type=float,
                default=0,
            ),
            OpenApiParameter(
                name="categories",
                description="Category IDs (comma-separated)",
                type=str,
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """Get deals near a specific location."""
        try:
            latitude = float(request.query_params.get("latitude"))
            longitude = float(request.query_params.get("longitude"))
        except (ValueError, TypeError):
            return Response(
                {"error": "Valid latitude and longitude are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius_km = float(request.query_params.get("radius", 10))
        limit = int(request.query_params.get("limit", 20))
        min_sustainability = float(request.query_params.get("min_sustainability", 0))

        categories = request.query_params.get("categories")
        category_ids = None
        if categories:
            category_ids = [int(c) for c in categories.split(",")]

        deals = DealService.get_deals_near_location(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
            min_sustainability=min_sustainability,
            categories=category_ids,
        )

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)
