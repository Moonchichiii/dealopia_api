from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.deals.models import Deal
from core.utils.cache import invalidate_cache_prefix


@receiver(post_save, sender=Deal)
def handle_deal_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Deal post_save.
    Sends notifications for new verified deals and invalidates related caches.
    """
    if created and instance.is_verified:
        try:
            from apps.deals.tasks import send_deal_notifications
            send_deal_notifications.delay(instance.id)
        except ImportError as e:
            print(f"Error importing send_deal_notifications: {e}")

    invalidate_deal_caches(instance)


@receiver(post_delete, sender=Deal)
def handle_deal_post_delete(sender, instance, **kwargs):
    """
    Signal handler for Deal post_delete.
    Invalidates all caches related to the deleted deal.
    """
    invalidate_deal_caches(instance)


def invalidate_deal_caches(deal):
    """
    Invalidate all caches related to a specific deal.
    Includes featured, category, expiring, new, related, and shop caches.
    """
    invalidate_cache_prefix("featured_deals")

    # Invalidate category caches
    for category in deal.categories.all():
        invalidate_cache_prefix(f"category:{category.id}")

    now = timezone.now()

    # Expiring deals cache
    if deal.end_date <= now + timezone.timedelta(days=3):
        invalidate_cache_prefix("expiring_deals")

    # New deals cache
    if deal.created_at >= now - timezone.timedelta(days=7):
        invalidate_cache_prefix("new_deals")

    invalidate_cache_prefix("related_deals")
    invalidate_cache_prefix("popular_deals")
    invalidate_cache_prefix(f"shop:{deal.shop_id}")
