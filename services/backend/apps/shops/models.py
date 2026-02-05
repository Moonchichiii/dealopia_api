from django.db import models
from django.utils.translation import gettext_lazy as _


def default_dict():
    """Default empty dict for JSON fields."""
    return {}


def default_list():
    """Default empty list for JSON fields."""
    return []


class Shop(models.Model):
    """
    Represents a shop/business entity with its details, location, and sustainability metrics.
    """

    name = models.CharField(_("Name"), max_length=255)
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="shops",
        verbose_name=_("Owner"),
    )
    description = models.TextField(_("Description"))
    short_description = models.CharField(_("Short Description"), max_length=255)
    logo = models.ImageField(_("Logo"), upload_to="shop_logos/", blank=True, null=True)
    banner_image = models.ImageField(
        _("Banner Image"), upload_to="shop_banners/", blank=True, null=True
    )
    website = models.URLField(_("Website"), blank=True)
    phone = models.CharField(_("Phone"), max_length=15, blank=True)
    email = models.EmailField(_("Email"))
    categories = models.ManyToManyField(
        "categories.Category", related_name="shops", verbose_name=_("Categories")
    )
    location = models.ForeignKey(
        "locations.Location", on_delete=models.PROTECT, verbose_name=_("Location")
    )
    is_verified = models.BooleanField(_("Verified"), default=False)
    is_featured = models.BooleanField(_("Featured"), default=False)
    rating = models.DecimalField(
        _("Rating"), max_digits=3, decimal_places=2, default=0.0
    )
    opening_hours = models.JSONField(_("Opening Hours"), default=default_dict)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    # Sustainability metrics
    carbon_neutral = models.BooleanField(_("Carbon Neutral"), default=False)
    sustainability_initiatives = models.JSONField(
        _("Sustainability Initiatives"), default=default_list, blank=True
    )
    verified_sustainable = models.BooleanField(_("Verified Sustainable"), default=False)
    # Sustainability score field
    sustainability_score = models.DecimalField(
        _("Sustainability Score"),
        max_digits=4,
        decimal_places=2,
        default=5.0,
        help_text=_("A score representing the shop's sustainability performance"),
    )

    class Meta:
        verbose_name = _("Shop")
        verbose_name_plural = _("Shops")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_verified", "is_featured"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return self.name

    @property
    def active_deals_count(self):
        """Get count of active deals for this shop."""
        from django.utils import timezone

        return self.deals.filter(
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        ).count()

    @property
    def featured_deals(self):
        """Get featured deals for this shop."""
        from django.utils import timezone

        return self.deals.filter(
            is_verified=True,
            is_featured=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        ).order_by("-created_at")

    def has_category(self, category_id):
        """Check if shop belongs to a specific category."""
        return self.categories.filter(id=category_id).exists()

    def update_rating(self):
        """Update shop rating based on reviews."""
        # Since there might not be a reviews relationship in testing,
        # we need to handle that case gracefully
        if not hasattr(self, "reviews"):
            return self.rating

        from django.db.models import Avg

        avg_rating = (
            self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"))["avg"]
            or 0
        )
        self.rating = round(avg_rating, 2)
        self.save(update_fields=["rating"])
        return self.rating


class Review(models.Model):
    """
    Represents a customer review for a shop.
    """

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    is_approved = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.shop.name} by {self.user or 'Anonymous'}"
