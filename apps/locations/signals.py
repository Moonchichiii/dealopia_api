from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.locations.models import Location


@receiver(post_save, sender=Location)
def location_saved(sender, instance, **kwargs):
    """Clear caches when a location is saved."""
    cache.delete(f"location:{instance.id}")
    cache.delete_pattern(f"popular_cities:*")
    cache.delete_pattern(f"locations_in_city:{instance.city.lower()}:*")
    cache.delete("location_stats")


@receiver(post_delete, sender=Location)
def location_deleted(sender, instance, **kwargs):
    """Clear caches when a location is deleted."""
    cache.delete(f"location:{instance.id}")
    cache.delete_pattern(f"popular_cities:*")
    cache.delete_pattern(f"locations_in_city:{instance.city.lower()}:*")
    cache.delete("location_stats")
