from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.products.models import Product
from core.utils.cache import invalidate_cache_prefix


@receiver(post_save, sender=Product)
def handle_product_post_save(sender, instance, created, **kwargs):
    """Signal handler for Product post_save"""
    # Invalidate product cache
    invalidate_cache_prefix(f"product:{instance.id}")

    # Invalidate shop's products cache
    invalidate_cache_prefix(f"shop_products:{instance.shop_id}")

    # Invalidate category-related caches
    for category in instance.categories.all():
        invalidate_cache_prefix(f"category_products:{category.id}")

    # Invalidate popular products cache
    invalidate_cache_prefix("popular_products")

    # Invalidate featured products cache if product is featured
    if instance.is_featured:
        invalidate_cache_prefix("featured_products")

    # If availability changed, invalidate product counts
    if "is_available" in kwargs.get("update_fields", []):
        invalidate_cache_prefix(f"shop_product_count:{instance.shop_id}")


@receiver(post_delete, sender=Product)
def handle_product_post_delete(sender, instance, **kwargs):
    """Signal handler for Product post_delete"""
    # Invalidate product cache
    invalidate_cache_prefix(f"product:{instance.id}")

    # Invalidate shop's products cache
    invalidate_cache_prefix(f"shop_products:{instance.shop_id}")

    # Invalidate category-related caches
    for category in instance.categories.all():
        invalidate_cache_prefix(f"category_products:{category.id}")

    # Invalidate popular products cache
    invalidate_cache_prefix("popular_products")

    # Invalidate featured products cache if product was featured
    if instance.is_featured:
        invalidate_cache_prefix("featured_products")

    # Invalidate product counts
    invalidate_cache_prefix(f"shop_product_count:{instance.shop_id}")
