from celery import shared_task
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
import requests

from apps.deals.models import Deal
from apps.scrapers.services import ScraperService
from apps.shops.models import Shop
from core.utils.cache import invalidate_cache_prefix


@shared_task
def send_deal_notifications(deal_id):
    pass


@shared_task
def update_sustainability_data():
    """Regularly fetch sustainability data from external sources"""
    # Update eco certifications
    scraper_service = ScraperService()
    scraper_service.fetch_eco_certifications()
    
    # Update carbon neutrality status for shops
    carbon_data = requests.get('https://carbon-api.example.com/businesses')
    for business in carbon_data.json()['businesses']:
        try:
            shop = Shop.objects.get(external_id=business['id'])
            shop.carbon_neutral = business['carbon_neutral']
            shop.save(update_fields=['carbon_neutral'])
        except Shop.DoesNotExist:
            continue
    
    # Update deals' sustainability scores
    Deal.objects.filter(is_active=True).select_related().iterator(chunk_size=100)
    for deal in Deal.objects.filter(is_active=True):
        deal.calculate_sustainability_score()


@receiver(post_save, sender=Deal)
def handle_deal_post_save(sender, instance, created, **kwargs):
    """Signal handler for Deal post_save"""
    if created and instance.is_verified:
        send_deal_notifications.delay(instance.id)
    
    invalidate_deal_caches(instance)


@receiver(post_delete, sender=Deal)
def handle_deal_post_delete(sender, instance, **kwargs):
    """Signal handler for Deal post_delete"""
    invalidate_deal_caches(instance)


def invalidate_deal_caches(deal):
    """Invalidate all caches related to a specific deal"""
    invalidate_cache_prefix("featured_deals")
    
    # Category-specific caches
    categories = deal.categories.values_list('id', flat=True)
    for category_id in categories:
        invalidate_cache_prefix(f"category:{category_id}")
    
    now = timezone.now()
    
    # Expiring deals cache
    if deal.end_date and deal.end_date <= now + timezone.timedelta(days=3):
        invalidate_cache_prefix("expiring_deals")
    
    # New deals cache
    if deal.created_at >= now - timezone.timedelta(days=7):
        invalidate_cache_prefix("new_deals")
    
    invalidate_cache_prefix("related_deals")
    invalidate_cache_prefix("popular_deals")
    invalidate_cache_prefix(f"shop:{deal.shop_id}")
