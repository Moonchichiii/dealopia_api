from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db.models import Count, Q

from apps.locations.geocoding import external_geocode_api
from apps.locations.models import Location


class LocationService:
    """Service class for location-related operations."""

    @staticmethod
    def get_nearby_locations(lat, lng, radius_km, limit=50):
        """
        Find locations within a specified radius from coordinates.

        Args:
            lat: Latitude as a float
            lng: Longitude as a float
            radius_km: Search radius in kilometers
            limit: Maximum number of results to return (default: 50)

        Returns:
            List of Location objects sorted by distance
        """
        point = Point(float(lng), float(lat), srid=4326)

        cache_key = f"nearby:{lat:.4f},{lng:.4f}:{radius_km}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        qs = (
            Location.objects.filter(coordinates__dwithin=(point, D(km=radius_km)))
            .annotate(distance=Distance("coordinates", point))
            .order_by("distance")[:limit]
        )

        results = list(qs)
        cache.set(cache_key, results, 3600)
        return results

    @staticmethod
    def get_deals_summary_for_locations(location_qs):
        """
        Annotate locations with their related deal counts.

        Args:
            location_qs: A queryset of Location objects

        Returns:
            The queryset annotated with deal_count
        """
        return location_qs.annotate(
            deal_count=Count("shop__deals", filter=Q(shop__deals__is_verified=True))
        )

    @staticmethod
    def geocode_address(address):
        """
        Convert an address string to a geospatial Point.

        Args:
            address: String address to geocode

        Returns:
            Point object or None if geocoding fails
        """
        try:
            lat, lng = external_geocode_api(address)
            if lat and lng:
                return Point(float(lng), float(lat), srid=4326)
        except Exception:
            pass
        return None
