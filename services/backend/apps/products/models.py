from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.shops.models import Shop


def default_dimensions():
    """Default empty dict for dimensions field"""
    return {"length": 0, "width": 0, "height": 0}


class Product(models.Model):
    """
    Represents a product sold by a shop with detailed specifications
    and inventory tracking.
    """

    WEIGHT_UNIT_CHOICES = [
        ("g", "Grams"),
        ("kg", "Kilograms"),
        ("lb", "Pounds"),
        ("oz", "Ounces"),
    ]

    # Basic information
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name="products", verbose_name=_("Shop")
    )
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    categories = models.ManyToManyField(
        "categories.Category",
        related_name="products",
        verbose_name=_("Categories"),
        blank=True,
    )

    # Inventory information
    stock_quantity = models.PositiveIntegerField(_("Stock Quantity"), default=0)
    sku = models.CharField(_("SKU"), max_length=50, unique=True, null=True, blank=True)
    barcode = models.CharField(_("Barcode"), max_length=50, blank=True)
    is_available = models.BooleanField(_("Available"), default=True)

    # Discounts
    discount_percentage = models.DecimalField(
        _("Discount Percentage"),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
    )

    # Physical attributes
    weight = models.DecimalField(_("Weight"), max_digits=8, decimal_places=3, default=0)
    weight_unit = models.CharField(
        _("Weight Unit"), max_length=2, choices=WEIGHT_UNIT_CHOICES, default="g"
    )
    dimensions = models.JSONField(
        _("Dimensions (cm)"),
        default=default_dimensions,
        help_text=_("JSON object with length, width, and height in cm"),
        null=True,
        blank=True,
    )

    # Tracking and analytics
    view_count = models.PositiveIntegerField(_("View Count"), default=0)
    purchase_count = models.PositiveIntegerField(_("Purchase Count"), default=0)
    is_featured = models.BooleanField(_("Featured"), default=False)

    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    # Extra fields
    image = models.ImageField(_("Main Image"), upload_to="product_images/", blank=True)
    additional_images = models.JSONField(
        _("Additional Images"), default=list, blank=True, null=True
    )
    specifications = models.JSONField(
        _("Specifications"), default=dict, blank=True, null=True
    )
    sustainability_score = models.DecimalField(
        _("Sustainability Score"),
        max_digits=4,
        decimal_places=2,
        default=5.0,
        help_text=_("A score representing the product's sustainability"),
    )
    meta_title = models.CharField(_("Meta Title"), max_length=255, blank=True)
    meta_description = models.CharField(
        _("Meta Description"), max_length=255, blank=True
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["is_available"]),
            models.Index(fields=["discount_percentage"]),
            models.Index(fields=["is_featured"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.shop.name})"

    # Price-related properties
    @property
    def discounted_price(self):
        """Calculate the discounted price based on discount percentage"""
        if self.discount_percentage > 0:
            discount_factor = Decimal("1") - (self.discount_percentage / Decimal("100"))
            return round(self.price * discount_factor, 2)
        return self.price

    @property
    def discount_amount(self):
        """Calculate the discount amount"""
        if self.discount_percentage > 0:
            return round(self.price - self.discounted_price, 2)
        return Decimal("0.00")

    # Tracking methods
    def update_view_count(self):
        """Increment view count by 1"""
        self.view_count += 1
        self.save(update_fields=["view_count"])

    def update_purchase_count(self, quantity=1):
        """Increment purchase count by the specified quantity"""
        self.purchase_count += quantity
        self.save(update_fields=["purchase_count"])

    # Inventory management
    def update_stock(self, quantity):
        """Update stock quantity and availability status"""
        old_quantity = self.stock_quantity
        self.stock_quantity = quantity

        # Auto-update availability based on stock
        if quantity <= 0 and self.is_available:
            self.is_available = False
        elif quantity > 0 and not self.is_available and old_quantity <= 0:
            self.is_available = True

        self.save(update_fields=["stock_quantity", "is_available", "updated_at"])

    # Deal-related methods
    def get_active_deals(self):
        """
        Get all active deals applicable to this product.
        First, try to get deals from the product's shop that apply
        to the product's categories. If no categories are assigned,
        return all active deals from the shop.
        """
        now = timezone.now()
        # Get deals from the shop that are active.
        shop_deals = self.shop.deals.filter(
            is_verified=True, start_date__lte=now, end_date__gte=now
        )
        # Get the category IDs for this product.
        category_ids = list(self.categories.values_list("id", flat=True))
        if category_ids:
            # Filter shop deals that target these categories.
            category_deals = shop_deals.filter(categories__id__in=category_ids)
            return category_deals
        # Fallback: return all active shop deals.
        return shop_deals

    def get_best_deal(self):
        """Get the best active deal for this product based on discount percentage"""
        deals = self.get_active_deals()
        if deals and deals.exists():
            return deals.order_by("-discount_percentage").first()
        return None
