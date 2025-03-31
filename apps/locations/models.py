from django.contrib.gis.db import models as gis_models
from django.db import models


class Location(models.Model):
    """Geospatial location model with optimized indexing."""

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=20)
    point = gis_models.PointField(spatial_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "country"]),
            models.Index(fields=["postal_code"]),
        ]

    def __str__(self):
        return f"{self.address}, {self.city}, {self.country}"

    @property
    def latitude(self):
        return self.point.y if self.point else None

    @property
    def longitude(self):
        return self.point.x if self.point else None

    @classmethod
    def in_country(cls, country):
        """Get locations in a specific country."""
        return cls.objects.filter(country__iexact=country)

    @classmethod
    def in_city(cls, city, country=None):
        """Get locations in a specific city."""
        query = cls.objects.filter(city__iexact=city)
        if country:
            query = query.filter(country__iexact=country)
        return query
