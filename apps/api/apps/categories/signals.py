from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.categories.models import Category
from apps.deals.models import Deal


@receiver([post_save, post_delete], sender=Deal)
def update_category_deal_counts(sender, instance, **kwargs):
    """
    Update active deal count for categories when deal objects change.

    Updates the cached deal count for each category associated with the deal
    when a deal is created, updated, or deleted.
    """
    for category in instance.categories.all():
        # Calculate the active deals count
        active_count = category.deals.filter(is_verified=True).count()

        # Update cache
        cache_key = f"category_{category.id}_active_deals_count"
        cache.set(cache_key, active_count, timeout=3600)

        print(
            f"Updated active deals count for category {category.id}: " f"{active_count}"
        )
