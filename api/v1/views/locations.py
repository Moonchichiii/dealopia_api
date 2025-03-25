from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from apps.locations.models import Location
from api.v1.serializers.locations import LocationSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['city', 'state', 'country', 'postal_code']
    
    @action(detail=False)
    def nearby(self, request):
        """Find locations near a specific point"""
        try:
            latitude = request.query_params.get('lat')
            longitude = request.query_params.get('lng')
            radius = float(request.query_params.get('radius', 10))
           
            if not latitude or not longitude:
                return Response({"error": "Latitude and longitude parameters are required"}, status=400)
           
            try:
                point = Point(float(longitude), float(latitude), srid=4326)
                radius = max(0.1, radius)
                
                locations = Location.objects.annotate(
                    distance=Distance('point', point)
                ).filter(distance__lte=radius * 1000).order_by('distance')
               
                serializer = self.get_serializer(locations, many=True)
                return Response(serializer.data)
            except ValueError:
                return Response({"error": "Invalid coordinates or radius value"}, status=400)
        except Exception as e:
            return Response({"error": f"Could not process location request: {str(e)}"}, status=400)
