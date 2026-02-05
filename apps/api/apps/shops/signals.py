from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.shops.models import Shop
from core.utils.cache import invalidate_cache_prefix


@receiver(post_save, sender=Shop)
def handle_shop_post_save(sender, instance, created, **kwargs):
    """Signal handler for Shop post_save"""
    invalidate_cache_prefix(f"shop:{instance.id}")
    invalidate_cache_prefix("featured_shops")
    invalidate_cache_prefix("popular_shops")


@receiver(post_delete, sender=Shop)
def handle_shop_post_delete(sender, instance, **kwargs):
    """Signal handler for Shop post_delete"""
    invalidate_cache_prefix(f"shop:{instance.id}")
    invalidate_cache_prefix("featured_shops")
    invalidate_cache_prefix("popular_shops")
