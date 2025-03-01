from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.apps.locations.models import Location

@receiver(post_save, sender=Location)
def handle_location_post_save(sender, instance, created, **kwargs):
    """Signal handler for Location post_save"""
    pass
