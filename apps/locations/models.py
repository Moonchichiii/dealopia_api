from django.contrib.gis.db import models as gis_models
from django.db import models

from core.managers.base import BaseManager


class LocationQuerySet(models.QuerySet):
    """Custom QuerySet for Location model"""
    
    def in_country(self, country):
        """Filter locations by country"""
        return self.filter(country__iexact=country)
    
    def in_city(self, city):
        """Filter locations by city"""
        return self.filter(city__iexact=city)
    
    def with_postal_code(self, postal_code):
        """Filter locations by postal code"""
        return self.filter(postal_code=postal_code)


class Location(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, db_index=True)
    postal_code = models.CharField(max_length=20)
    point = gis_models.PointField(spatial_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = BaseManager.from_queryset(LocationQuerySet)()
    
    class Meta:
        indexes = [
            models.Index(fields=['city', 'country']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['city', 'country', 'postal_code']),
        ]
        
    def __str__(self):
        return f"{self.address}, {self.city}, {self.country}"
    
    @property
    def latitude(self):
        return self.point.y if self.point else None
    
    @property
    def longitude(self):
        return self.point.x if self.point else None
    
    def get_coordinates(self):
        """Get coordinates as a tuple (latitude, longitude)"""
        if self.point:
            return (self.point.y, self.point.x)
        return None
