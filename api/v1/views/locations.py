from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.v1.serializers.locations import LocationSerializer
from apps.locations.models import Location
from apps.locations.services import LocationService


class LocationViewSet(viewsets.ModelViewSet):
    """API endpoint for locations with geospatial search capabilities."""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'city', 'postal_code']
    search_fields = ['city', 'state', 'country', 'postal_code', 'address']
    ordering_fields = ['created_at', 'city', 'country']
    ordering = ['country', 'city']
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='lat', description='Latitude', required=True, type=float),
            OpenApiParameter(name='lng', description='Longitude', required=True, type=float),
            OpenApiParameter(name='radius', description='Radius in kilometers', type=float, default=10.0),
            OpenApiParameter(name='limit', description='Maximum number of results to return', type=int, default=20)
        ]
    )
    @action(detail=False)
    def nearby(self, request):
        """Find locations near a specific point"""
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        
        if not latitude or not longitude:
            return Response(
                {"error": "Latitude and longitude parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
            radius = min(max(0.1, float(request.query_params.get('radius', 10))), 50)  # Between 100m and 50km
            limit = min(max(1, int(request.query_params.get('limit', 20))), 100)  # Between 1 and 100 results
            
            locations = LocationService.get_nearby_locations(lat, lng, radius, limit)
            serializer = self.get_serializer(locations, many=True)
            
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {"error": "Invalid coordinates or radius value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Could not process location request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='country', description='Country code', required=False),
            OpenApiParameter(name='limit', description='Maximum number of cities to return', type=int, default=10)
        ]
    )
    @action(detail=False)
    def popular_cities(self, request):
        """Get popular cities based on location count"""
        try:
            country = request.query_params.get('country')
            limit = min(max(1, int(request.query_params.get('limit', 10))), 50)  # Between 1 and 50 results
            
            popular_cities = LocationService.get_popular_cities(country, limit)
            return Response(popular_cities)
        except Exception as e:
            return Response(
                {"error": f"Could not retrieve popular cities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False)
    def stats(self, request):
        """Get location statistics"""
        try:
            return Response(LocationService.get_location_stats())
        except Exception as e:
            return Response(
                {"error": f"Could not retrieve location statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
