from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.apps.categories.models import Category

@receiver(post_save, sender=Category)
def handle_category_post_save(sender, instance, created, **kwargs):
    """Signal handler for Category post_save"""
    pass
