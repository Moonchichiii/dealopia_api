from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.apps.accounts.models import User

@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """Signal handler for User post_save"""
    if created:
        # Add any initialization logic here
        pass
