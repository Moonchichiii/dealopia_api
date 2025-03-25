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
    
    sustainability_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    eco_certifications = models.JSONField(default=list, blank=True)
    
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
        
    def calculate_sustainability_score(self):
        """Calculate score based on certifications, shop ratings, and categories"""
        base_score = 0
        
        # Add points for eco certifications
        cert_points = min(len(self.eco_certifications) * 1.5, 5)
        base_score += cert_points
        
        # Add points for shop sustainability
        if self.shop.carbon_neutral:
            base_score += 2
        
        # Add points for eco-friendly categories
        eco_categories = self.categories.filter(is_eco_friendly=True).count()
        category_points = min(eco_categories * 1, 3)
        base_score += category_points
        
        # Normalize to 0-10 scale
        self.sustainability_score = min(base_score, 10)
        self.save(update_fields=['sustainability_score'])
