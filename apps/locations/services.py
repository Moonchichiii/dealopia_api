from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db.models import Count

from core.utils.cache import cache_result
from .models import Location


class LocationService:
    """Service for location-related business logic and geospatial operations."""
    
    @staticmethod
    @cache_result(timeout=86400, prefix="location")
    def get_location_by_id(location_id):
        """Get a location by ID with caching"""
        try:
            return Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return None

    @staticmethod
    @cache_result(timeout=3600, prefix="nearby_locations")
    def get_nearby_locations(latitude, longitude, radius_km=10, limit=None):
        """Find locations near a specific point"""
        user_location = Point(longitude, latitude, srid=4326)
        radius = max(0.1, min(radius_km, 50))  # Between 100m and 50km
        
        locations = Location.objects.annotate(
            distance=Distance('point', user_location)
        ).filter(
            point__distance_lte=(user_location, D(km=radius))
        ).order_by('distance')
        
        if limit:
            locations = locations[:limit]
            
        return locations
    
    @staticmethod
    @cache_result(timeout=86400, prefix="popular_cities")
    def get_popular_cities(country=None, limit=10):
        """Get popular cities based on location count"""
        queryset = Location.objects.values('city', 'country')
        
        if country:
            queryset = queryset.filter(country=country)
            
        return queryset.annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
    
    @staticmethod
    def create_or_update_location(address, city, state, country, postal_code, latitude, longitude):
        """Create or update a location"""
        point = Point(float(longitude), float(latitude), srid=4326)
        
        location = Location.objects.filter(
            address=address,
            city=city,
            country=country
        ).first()
        
        if location:
            location.state = state
            location.postal_code = postal_code
            location.point = point
            location.save()
        else:
            location = Location.objects.create(
                address=address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                point=point
            )
            
        # Invalidate relevant caches
        cache_keys = [
            f"popular_cities",
            f"popular_cities:{country}" 
        ]
        for key in cache_keys:
            cache.delete(key)
            
        return location
    
    @staticmethod
    @cache_result(timeout=3600, prefix="locations_in_city")
    def get_locations_in_city(city, country=None):
        """Get all locations in a specific city"""
        queryset = Location.objects.filter(city__iexact=city)
        
        if country:
            queryset = queryset.filter(country__iexact=country)
            
        return queryset
    
    @staticmethod
    def get_location_stats():
        """Get statistics about locations"""
        total_count = Location.objects.count()
        countries_count = Location.objects.values('country').distinct().count()
        cities_count = Location.objects.values('city', 'country').distinct().count()
        
        top_countries = Location.objects.values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'total_locations': total_count,
            'countries_count': countries_count,
            'cities_count': cities_count,
            'top_countries': list(top_countries)
        }
