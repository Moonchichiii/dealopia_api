import logging
from typing import Optional

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
    """
    API endpoint for deals. Supports:
      - Text search and filtering.
      - Geospatial filtering (to show local deals).
    """
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsShopOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
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
        """
        If latitude and longitude are provided in query parameters,
        filter deals that are local (within a 100 km radius) and meet a minimum sustainability score.
        """
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        min_score = float(request.query_params.get("min_score", 5.0))
        if latitude and longitude:
            queryset = DealService.get_local_and_sustainable_deals(
                float(latitude), float(longitude), radius_km=100, min_score=min_score
            )
        else:
            queryset = DealService.get_active_deals().filter(sustainability_score__gte=min_score)

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
            OpenApiParameter(name="min_score", description="Minimum sustainability score", type=float),
            OpenApiParameter(name="limit", description="Result limit", type=int),
        ]
    )
    @action(detail=False)
    def sustainable(self, request):
        try:
            min_score = float(request.query_params.get("min_score", 7.0))
            limit = int(request.query_params.get("limit", 10))
            deals = DealService.get_sustainable_deals(min_score, limit)
            serializer = self.get_serializer(deals, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def track_view(self, request, pk=None):
        DealService.record_interaction(pk, "view")
        return Response({"status": "view recorded"})

    @action(detail=True, methods=["post"])
    def track_click(self, request, pk=None):
        DealService.record_interaction(pk, "click")
        return Response({"status": "click recorded"})
