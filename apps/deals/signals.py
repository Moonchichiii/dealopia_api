from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.deals.models import Deal
from apps.deals.tasks import send_deal_notifications

@receiver(post_save, sender=Deal)
def handle_deal_post_save(sender, instance, created, **kwargs):
    """Signal handler for Deal post_save"""
    if created and instance.is_verified:
        # Send notifications about the new deal
        send_deal_notifications.delay(instance.id)
