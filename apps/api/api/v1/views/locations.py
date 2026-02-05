import re
from functools import partial

from django.contrib.gis.db.models import PointField
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.v1.serializers.deals import DealSerializer
from api.v1.serializers.locations import LocationSerializer
from apps.deals.services import DealService
from apps.locations.models import Location
from apps.locations.services import LocationService


class LocationViewSet(viewsets.ModelViewSet):
    """API endpoint for managing locations with geospatial capabilities."""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["country", "city", "postal_code"]
    search_fields = ["city", "state", "country", "postal_code", "address"]
    ordering_fields = ["city", "country", "created_at"]
    ordering = ["country", "city"]

    def list(self, request, *args, **kwargs):
        """Return a plain list of location objects."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _get_bounded_param(self, value, default, min_val, max_val, converter=float):
        """Utility for bounding float/int query parameters."""
        try:
            parsed = converter(value) if value is not None else default
            return max(min_val, min(parsed, max_val))
        except (ValueError, TypeError):
            return default

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="lat", description="Latitude", required=True, type=float
            ),
            OpenApiParameter(
                name="lng", description="Longitude", required=True, type=float
            ),
            OpenApiParameter(name="radius", type=float, default=10.0),
            OpenApiParameter(name="limit", type=int, default=20),
            OpenApiParameter(name="include_deals", type=bool, default=False),
            OpenApiParameter(
                name="deal_radius", type=float, description="Search radius for deals"
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """Return locations and optionally deals near specified coordinates."""
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid lat/lng"}, status=status.HTTP_400_BAD_REQUEST
            )

        get_float = partial(self._get_bounded_param, converter=float)
        get_int = partial(self._get_bounded_param, converter=int)

        radius = get_float(request.query_params.get("radius"), 10, 0.1, 50)
        limit = get_int(request.query_params.get("limit"), 20, 1, 500)
        include_deals = (
            request.query_params.get("include_deals", "false").lower() == "true"
        )

        deal_radius_str = request.query_params.get("deal_radius")
        if deal_radius_str:
            deal_radius = get_float(deal_radius_str, 10, 0.1, 50)
        else:
            deal_radius = radius

        locations = LocationService.get_nearby_locations(lat, lng, radius, limit)
        data = {"locations": self.get_serializer(locations, many=True).data}

        if include_deals:
            deals = DealService.get_deals_near_location(lat, lng, deal_radius)
            data["deals"] = DealSerializer(
                deals, many=True, context=self.get_serializer_context()
            ).data

        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="country", type=str),
            OpenApiParameter(name="limit", type=int),
        ]
    )
    @action(detail=False, methods=["get"])
    def popular_cities(self, request):
        """Return most popular cities based on location count."""
        country = request.query_params.get("country")
        limit = self._get_bounded_param(
            request.query_params.get("limit"), 10, 1, 100, converter=int
        )

        qs = Location.objects.all()
        if country:
            qs = qs.filter(country__iexact=country)

        cities = (
            qs.values("city")
            .annotate(count=models.Count("id"))
            .order_by("-count")[:limit]
        )
        results = [{"city": c["city"], "count": c["count"]} for c in cities]
        return Response(results)

    @extend_schema()
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Return overall location statistics."""
        total = Location.objects.count()
        country_stats = (
            Location.objects.values("country")
            .annotate(count=models.Count("id"))
            .order_by("-count")
        )
        data = {
            "total_locations": total,
            "countries": [
                {"country": c["country"], "count": c["count"]} for c in country_stats
            ],
        }
        return Response(data)
