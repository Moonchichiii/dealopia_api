from celery import shared_task
from django.utils import timezone
from django.db.models import Count
from .models import Deal
from apps.categories.models import Category


@shared_task
def update_expired_deals():
    """Mark deals as expired if end_date has passed"""
    now = timezone.now()
    expired_count = Deal.objects.filter(
        end_date__lt=now, 
        is_verified=True
    ).update(is_verified=False)
    
    # If any deals were expired, we should warm the caches
    if expired_count > 0:
        warm_deal_caches.delay()
        
    return f"Marked {expired_count} deals as expired"


@shared_task
def send_deal_notifications(deal_id):
    """Send notifications for a new deal"""
    from apps.accounts.models import User
    from django.core.mail import send_mail
    
    try:
        deal = Deal.objects.get(id=deal_id)
        users = User.objects.filter(favorite_categories__in=deal.categories.all()).distinct()
        
        for user in users:
            # This would be replaced with a proper notification system
            print(f"Sending notification to {user.email} about deal: {deal.title}")
            
        return f"Notifications sent to {users.count()} users"
    except Deal.DoesNotExist:
        return "Deal not found"


@shared_task
def warm_deal_caches():
    """Pre-warm commonly accessed deal caches"""
    from apps.deals.services import DealService
    
    # Warm the most frequently accessed caches
    DealService.get_featured_deals()
    DealService.get_expiring_soon_deals()
    DealService.get_new_deals()
    DealService.get_popular_deals()
    
    # Warm popular category deals
    popular_categories = Category.objects.annotate(
        deal_count=Count('deals', filter=models.Q(deals__is_verified=True))
    ).filter(is_active=True).order_by('-deal_count')[:5]
    
    for category in popular_categories:
        # Assuming you've added this method to your service
        DealService.get_deals_by_category(category.id)
        
    return "Deal caches warmed successfully"


@shared_task
def update_deal_statistics():
    """Update aggregated deal statistics"""
    from django.db.models import Avg, Sum
    from django.core.cache import cache
    
    # Calculate average discount percentage
    avg_discount = Deal.objects.filter(
        is_verified=True
    ).aggregate(
        avg_discount=Avg('discount_percentage')
    )['avg_discount'] or 0
    
    # Calculate total savings (original - discounted)
    total_savings = Deal.objects.filter(
        is_verified=True
    ).aggregate(
        total=Sum(models.F('original_price') - models.F('discounted_price'))
    )['total'] or 0
    
    # Store metrics in cache
    cache.set('stats:avg_discount', avg_discount, 86400)  # 24 hours
    cache.set('stats:total_savings', total_savings, 86400)  # 24 hours
    
    return "Updated deal statistics"


@shared_task
def clean_outdated_deals(days=90):
    """
    Mark very old expired deals as inactive to keep the active dataset smaller
    This helps maintain database performance
    """
    threshold = timezone.now() - timezone.timedelta(days=days)
    
    count = Deal.objects.filter(
        end_date__lt=threshold,
        is_verified=True
    ).update(
        is_verified=False
    )
    
    return f"Cleaned {count} outdated deals"