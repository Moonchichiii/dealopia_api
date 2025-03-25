from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.deals.models import Deal
from apps.deals.tasks import send_deal_notifications
from core.utils.cache import invalidate_cache_prefix, CacheGroup


@receiver(post_save, sender=Deal)
def handle_deal_post_save(sender, instance, created, **kwargs):
    """Signal handler for Deal post_save"""
    # Send notifications for new verified deals
    if created and instance.is_verified:
        send_deal_notifications.delay(instance.id)
    
    # Invalidate relevant caches
    invalidate_deal_caches(instance)


@receiver(post_delete, sender=Deal)
def handle_deal_post_delete(sender, instance, **kwargs):
    """Signal handler for Deal post_delete"""
    # Invalidate relevant caches
    invalidate_deal_caches(instance)


def invalidate_deal_caches(deal):
    """Invalidate all caches related to a specific deal"""
    # Invalidate featured deals cache
    invalidate_cache_prefix("featured_deals")
    
    # Invalidate deals by category caches
    for category in deal.categories.all():
        invalidate_cache_prefix(f"category:{category.id}")
    
    # Invalidate expiring deals if this deal is expiring soon
    now = timezone.now()
    three_days_later = now + timezone.timedelta(days=3)
    if deal.end_date <= three_days_later:
        invalidate_cache_prefix("expiring_deals")
    
    # Invalidate new deals if this is a new deal
    week_ago = now - timezone.timedelta(days=7)
    if deal.created_at >= week_ago:
        invalidate_cache_prefix("new_deals")
    
    # Invalidate related deals caches
    invalidate_cache_prefix("related_deals")
    
    # Invalidate popular deals if this is a popular deal
    # This is a simple heuristic - you might want to be more selective
    invalidate_cache_prefix("popular_deals")
    
    # Invalidate shop-specific caches
    invalidate_cache_prefix(f"shop:{deal.shop_id}")