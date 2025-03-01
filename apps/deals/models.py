from django.db import models

class Deal(models.Model):
    title = models.CharField(max_length=255)
    shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='deals')
    description = models.TextField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.PositiveIntegerField()
    categories = models.ManyToManyField('categories.Category', related_name='deals')
    image = models.ImageField(upload_to='deal_images/')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_featured = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)
    terms_and_conditions = models.TextField(blank=True)
    coupon_code = models.CharField(max_length=50, blank=True)
    redemption_link = models.URLField(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['discount_percentage']),
            models.Index(fields=['shop']),
        ]
        
    def __str__(self):
        return self.title
