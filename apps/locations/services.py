from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db.models import Count

from .models import Location


class LocationService:
    """Streamlined service for location operations with optimized spatial queries."""

    @staticmethod
    def get_location_by_id(location_id):
        """Get a location by ID with efficient caching."""
        cache_key = f"location:{location_id}"
        location = cache.get(cache_key)

        if not location:
            try:
                location = Location.objects.get(id=location_id)
                cache.set(cache_key, location, 86400)  # Cache for 24 hours
            except Location.DoesNotExist:
                return None

        return location

    @staticmethod
    def get_nearby_locations(latitude, longitude, radius_km=10, limit=20):
        """Find locations near a point with optimized spatial indexing."""
        # Create a point from coordinates
        user_location = Point(longitude, latitude, srid=4326)

        # Use ST_DWithin for better index usage (more efficient than distance calculations)
        locations = (
            Location.objects.filter(point__dwithin=(user_location, D(km=radius_km)))
            .annotate(distance=Distance("point", user_location))
            .order_by("distance")[:limit]
        )

        return locations

    @staticmethod
    def get_popular_cities(country=None, limit=10):
        """Get most common cities in the database."""
        cache_key = f"popular_cities:{country or 'all'}:{limit}"
        result = cache.get(cache_key)

        if not result:
            queryset = Location.objects.values("city", "country")
            if country:
                queryset = queryset.filter(country__iexact=country)

            result = list(
                queryset.annotate(count=Count("id")).order_by("-count")[:limit]
            )

            cache.set(cache_key, result, 3600)  # Cache for 1 hour

        return result

    @staticmethod
    def create_or_update_location(
        address, city, state, country, postal_code, latitude, longitude
    ):
        """Efficiently create or update a location record."""
        point = Point(float(longitude), float(latitude), srid=4326)

        # Try to find existing location first
        location, created = Location.objects.update_or_create(
            address=address,
            city=city,
            country=country,
            defaults={"state": state, "postal_code": postal_code, "point": point},
        )

        # Clear relevant caches
        cache.delete_pattern(f"popular_cities:*")
        cache.delete_pattern(f"locations_in_city:{city.lower()}:*")

        return location

    @staticmethod
    def get_location_stats():
        """Get quick statistics about locations."""
        cache_key = "location_stats"
        stats = cache.get(cache_key)

        if not stats:
            stats = {
                "total_locations": Location.objects.count(),
                "countries_count": Location.objects.values("country")
                .distinct()
                .count(),
                "cities_count": Location.objects.values("city", "country")
                .distinct()
                .count(),
                "top_countries": list(
                    Location.objects.values("country")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5]
                ),
            }

            cache.set(cache_key, stats, 3600)  # Cache for 1 hour

        return stats
