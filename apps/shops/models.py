from django.db import models

class Shop(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='shops')
    description = models.TextField()
    short_description = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='shop_logos/')
    banner_image = models.ImageField(upload_to='shop_banners/', blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField()
    categories = models.ManyToManyField('categories.Category', related_name='shops')
    location = models.ForeignKey('locations.Location', on_delete=models.PROTECT)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    opening_hours = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_verified', 'is_featured']),
        ]
        
    def __str__(self):
        return self.name
