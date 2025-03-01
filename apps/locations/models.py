from django.contrib.gis.db import models as gis_models
from django.db import models

class Location(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    point = gis_models.PointField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['city', 'country']),
        ]
        
    def __str__(self):
        return f"{self.address}, {self.city}, {self.country}"
