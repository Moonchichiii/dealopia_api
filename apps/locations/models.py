from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.indexes import GistIndex
from django.db import models


class Location(models.Model):
    """
    Geospatial location model using a geography-enabled PointField.
    PostGIS must be set up, plus GDAL, GEOS, etc. in your environment.
    """

    name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=20, blank=True)
    coordinates = gis_models.PointField(
        srid=4326, geography=True, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "country"]),
            models.Index(fields=["postal_code"]),
            GistIndex(fields=["coordinates"]),
        ]

    def __str__(self):
        """Return a human-readable representation of the location."""
        return f"{self.address}, {self.city}, {self.country}"

    @property
    def latitude(self):
        """Return the Y coordinate if coordinates are set."""
        return self.coordinates.y if self.coordinates else None

    @property
    def longitude(self):
        """Return the X coordinate if coordinates are set."""
        return self.coordinates.x if self.coordinates else None

    @classmethod
    def in_country(cls, country):
        """Filter locations by country name (case-insensitive)."""
        return cls.objects.filter(country__iexact=country)

    @classmethod
    def in_city(cls, city, country=None):
        """
        Filter locations by city name and optionally by country.
        Both filters are case-insensitive.
        """
        qs = cls.objects.filter(city__iexact=city)
        if country:
            qs = qs.filter(country__iexact=country)
        return qs
