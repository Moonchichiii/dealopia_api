import re
from functools import partial

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.v1.serializers.locations import LocationSerializer
from apps.locations.models import Location
from apps.locations.services import LocationService


class LocationViewSet(viewsets.ModelViewSet):
    """API endpoint for locations with geospatial capabilities."""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["country", "city", "postal_code"]
    search_fields = ["city", "state", "country", "postal_code", "address"]
    ordering_fields = ["city", "country", "created_at"]
    ordering = ["country", "city"]

    def _get_bounded_param(self, value, default, min_val, max_val, converter=float):
        """Helper to parse and bound request parameters."""
        try:
            parsed = converter(value) if value is not None else default
            return max(min_val, min(parsed, max_val))
        except (ValueError, TypeError):
            return default

    @extend_schema(
        parameters=[
            OpenApiParameter(name="lat", description="Latitude", required=True, type=float),
            OpenApiParameter(name="lng", description="Longitude", required=True, type=float),
            OpenApiParameter(name="radius", description="Radius in kilometers", type=float, default=10.0),
            OpenApiParameter(name="limit", description="Maximum results", type=int, default=20),
        ]
    )
    @action(detail=False)
    def nearby(self, request):
        """Find locations near a specific point."""
        try:
            lat = float(request.query_params.get("lat", 0))
            lng = float(request.query_params.get("lng", 0))
            
            get_bounded_float = partial(self._get_bounded_param, converter=float)
            get_bounded_int = partial(self._get_bounded_param, converter=int)
            
            radius = get_bounded_float(request.query_params.get("radius"), 10, 0.1, 50)
            limit = get_bounded_int(request.query_params.get("limit"), 20, 1, 100)

            locations = LocationService.get_nearby_locations(lat, lng, radius, limit)
            serializer = self.get_serializer(locations, many=True)

            return Response(serializer.data)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid coordinates or parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(name="country", description="Country code"),
            OpenApiParameter(name="limit", description="Maximum cities", type=int, default=10),
        ]
    )
    @action(detail=False)
    def popular_cities(self, request):
        """Get popular cities based on database entries."""
        country = request.query_params.get("country")
        limit = self._get_bounded_param(
            request.query_params.get("limit"), 10, 1, 50, converter=int
        )

        cities = LocationService.get_popular_cities(country, limit)
        return Response(cities)

    @action(detail=False)
    def stats(self, request):
        """Get location statistics."""
        return Response(LocationService.get_location_stats())
