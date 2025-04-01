from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender="locations.Location")
def handle_location_saved(sender, instance, created, **kwargs):
    """Handle post-save operations for Location model."""
    transaction.on_commit(lambda: _on_location_saved(instance, created))


def _on_location_saved(location, created):
    """Handle post-commit logic for location save.
    
    Geocodes address if coordinates are missing and invalidates cache entries.
    """
    # Import here to avoid circular import
    from apps.locations.models import Location
    from apps.locations.services import LocationService

    if location.address and not location.coordinates:
        point = LocationService.geocode_address(location.address)
        if point:
            # Direct update to avoid recursive signal triggers
            Location.objects.filter(pk=location.pk).update(coordinates=point)

    # Invalidate nearby cache entries
    for key in cache.keys("nearby:*"):
        cache.delete(key)


@receiver(post_delete, sender="locations.Location")
def handle_location_deleted(sender, instance, **kwargs):
    """Invalidate cache entries when a location is deleted."""
    for key in cache.keys("nearby:*"):
        cache.delete(key)
