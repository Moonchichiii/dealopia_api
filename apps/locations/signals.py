from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# Import your location model here
# from apps.locations.models import Location

# Example signal handler:
# @receiver(post_save, sender=Location)
# def location_post_save(sender, instance, created, **kwargs):
#     """
#     Signal handler for when a location is saved
#     """
#     if created:
#         # Do something when a new location is created
#         pass
#     else:
#         # Do something when an existing location is updated
#         pass
