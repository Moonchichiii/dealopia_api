from celery import shared_task
from django.utils import timezone
from .models import Deal

@shared_task
def update_expired_deals():
    """Mark deals as expired if end_date has passed"""
    now = timezone.now()
    return Deal.objects.filter(end_date__lt=now, is_verified=True).update(is_verified=False)

@shared_task
def send_deal_notifications(deal_id):
    """Send notifications for a new deal"""
    from backend.apps.accounts.models import User
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
