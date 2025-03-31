from cloudinary.models import CloudinaryField
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Deal(models.Model):
    """
    Deal model with sustainability focus and efficient indexing.
    """

    title = models.CharField(max_length=255)
    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="deals"
    )
    description = models.TextField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.PositiveIntegerField()
    categories = models.ManyToManyField("categories.Category", related_name="deals")

    # Use Cloudinary for optimized image handling
    image = CloudinaryField(
        "image",
        transformation={"quality": "auto:good", "fetch_format": "auto"},
        folder="deals",
        resource_type="image",
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_featured = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)
    terms_and_conditions = models.TextField(blank=True)
    coupon_code = models.CharField(max_length=50, blank=True)
    redemption_link = models.URLField(blank=True)

    # Sustainability metrics with better defaults
    sustainability_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=0
    )
    eco_certifications = models.JSONField(default=list, blank=True)
    carbon_footprint = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    local_production = models.BooleanField(
        default=False, help_text="Item produced locally"
    )

    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Source tracking for API imported deals
    source = models.CharField(
        max_length=50, blank=True, help_text="Source API or scraper"
    )
    external_id = models.CharField(
        max_length=100, blank=True, help_text="ID in external system"
    )

    class Meta:
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["is_featured", "is_verified"]),
            models.Index(fields=["discount_percentage"]),
            models.Index(
                fields=["sustainability_score"]
            ),  # Index for sustainability queries
            models.Index(fields=["shop"]),
            # Compound index for common query patterns
            models.Index(fields=["is_verified", "start_date", "end_date"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        """Check if the deal is currently active."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_verified

    @property
    def discount_amount(self):
        """Calculate absolute discount amount."""
        return self.original_price - self.discounted_price

    @property
    def time_left(self):
        """Calculate time remaining until expiration."""
        now = timezone.now()
        if now > self.end_date:
            return None

        return self.end_date - now

    @classmethod
    def get_active(cls):
        """Get all active deals with optimized query."""
        now = timezone.now()
        return cls.objects.filter(
            is_verified=True, start_date__lte=now, end_date__gte=now
        )

    @classmethod
    def get_sustainable(cls, min_score=7.0):
        """Get active deals with good sustainability scores."""
        return cls.get_active().filter(sustainability_score__gte=min_score)

    def calculate_sustainability_score(self):
        """
        Calculate comprehensive sustainability score based on multiple factors.
        """
        score = 0

        # Base factors
        if self.eco_certifications:
            score += min(len(self.eco_certifications) * 1.5, 4.0)

        if self.local_production:
            score += 2.0

        # Shop factors
        if hasattr(self.shop, "carbon_neutral") and self.shop.carbon_neutral:
            score += 2.0

        if hasattr(self.shop, "sustainability_initiatives"):
            initiatives = getattr(self.shop, "sustainability_initiatives", [])
            if initiatives:
                score += min(len(initiatives) * 0.5, 1.5)

        # Category factors
        eco_categories = self.categories.filter(
            Q(is_eco_friendly=True)
            | Q(name__icontains="sustain")
            | Q(name__icontains="eco")
            | Q(name__icontains="green")
        ).count()
        score += min(eco_categories * 1.0, 2.5)

        # Carbon footprint (lower is better)
        if self.carbon_footprint is not None:
            if self.carbon_footprint < 5:
                score += 2.0
            elif self.carbon_footprint < 10:
                score += 1.0

        # Normalize score to max of 10
        score = min(score, 10.0)

        # Update model
        self.sustainability_score = score
        self.save(update_fields=["sustainability_score"])

        return score
