from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.apps.shops.models import Shop

@receiver(post_save, sender=Shop)
def handle_shop_post_save(sender, instance, created, **kwargs):
    """Signal handler for Shop post_save"""
    if created:
        # Add any initialization logic here
        pass
