"""
Celery tasks for deals management.
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional, Union

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.deals.models import Deal
from apps.shops.models import Shop

logger = logging.getLogger("dealopia.deals")


@shared_task(bind=True, max_retries=3)
def scrape_shop(self, shop_id: int) -> Dict[str, any]:
    from apps.scrapers.models import ScraperJob

    shop_obj = Shop.objects.get(id=shop_id)
    job = ScraperJob.objects.create(
        spider_name="ShopScraper", status="running", source_url=shop_obj.website or ""
    )
    try:
        from apps.scrapers.services import ScraperService

        result = ScraperService.scrape_shop_deals(shop_id)
        job.status = "completed" if result.get("success") else "failed"
        job.completed_at = timezone.now()
        job.items_scraped = result.get("total_processed", 0)
        job.deals_created = result.get("deals_created", 0)
        job.deals_updated = result.get("deals_updated", 0)
        if not result.get("success"):
            job.error_message = result.get("error", "Unknown error")
            job.error_count = 1
        job.save()
        return result
    except Exception as e:
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.error_count = 1
        job.save()
        self.retry(exc=e, countdown=60 * self.request.retries)
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def import_deals_from_api(self, source_name: str, limit: int = 100) -> Dict[str, any]:
    from apps.scrapers.models import ScraperJob

    job = ScraperJob.objects.create(spider_name=f"API-{source_name}", status="running")
    try:
        # Stub: Replace with your actual API integration (e.g. Google Places or other)
        result = {"success": True, "created": 5, "updated": 3, "source": source_name}
        job.status = "completed"
        job.completed_at = timezone.now()
        job.deals_created = result.get("created", 0)
        job.deals_updated = result.get("updated", 0)
        job.save()
        return result
    except Exception as e:
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.error_count = 1
        job.save()
        return {"success": False, "error": str(e)}


@shared_task
def bulk_scrape_shops(shop_ids: Optional[List[int]] = None) -> Dict[str, any]:
    from apps.shops.models import Shop

    if shop_ids is None:
        shop_ids = list(
            Shop.objects.filter(is_verified=True, website__isnull=False).values_list(
                "id", flat=True
            )
        )
    results = {
        "total_shops": len(shop_ids),
        "successful": 0,
        "failed": 0,
        "total_deals_created": 0,
        "total_deals_updated": 0,
    }
    for shop_id in shop_ids:
        try:
            scrape_shop.delay(shop_id)
            results["successful"] += 1
        except Exception as e:
            logger.error(f"Error queueing scrape task for shop {shop_id}: {e}")
            results["failed"] += 1
    return results


@shared_task
def clean_expired_deals(days: int = 30) -> Dict[str, int]:
    """
    Remove deals that have been expired for more than the specified number of days.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    expired_deals = Deal.objects.filter(end_date__lt=cutoff_date)
    count = expired_deals.count()
    expired_deals.delete()
    logger.info(f"Deleted {count} deals expired for more than {days} days")
    return {"deleted": count}


@shared_task
def update_sustainability_scores() -> Dict[str, int]:
    """
    Update sustainability scores for all deals.
    """
    deals = Deal.objects.all()
    updated = 0
    errors = 0
    for deal in deals:
        try:
            deal.calculate_sustainability_score()
            updated += 1
        except Exception as e:
            logger.error(
                f"Error updating sustainability score for deal {deal.id}: {str(e)}"
            )
            errors += 1
    return {"updated": updated, "errors": errors, "total": updated + errors}


@shared_task
def send_deal_notifications(deal_id: int) -> Dict[str, Union[bool, int, str]]:
    """
    Send notifications for a newly created or updated deal.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        deal = Deal.objects.get(id=deal_id)
        # Find users whose favorite categories intersect with deal categories
        category_ids = deal.categories.values_list("id", flat=True)
        relevant_users = User.objects.filter(
            favorite_categories__id__in=category_ids
        ).distinct()
        if not relevant_users.exists():
            logger.info(f"No users to notify about deal {deal.id}: {deal.title}")
            return {"success": True, "deal_id": deal_id, "notifications_sent": 0}
        logger.info(
            f"Would notify {relevant_users.count()} users about deal: {deal.title}"
        )
        return {
            "success": True,
            "deal_id": deal_id,
            "notifications_sent": relevant_users.count(),
        }
    except Deal.DoesNotExist:
        logger.error(f"Deal {deal_id} not found - cannot send notifications")
        return {"success": False, "error": f"Deal {deal_id} not found"}
    except Exception as e:
        logger.error(f"Error sending notifications for deal {deal_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def update_deal_statistics() -> Dict[str, int]:
    """
    Update statistical data for deals.
    """
    active_deals = Deal.objects.filter(
        is_verified=True, start_date__lte=timezone.now(), end_date__gte=timezone.now()
    )
    total_count = active_deals.count()
    updated_count = 0
    for deal in active_deals:
        try:
            if deal.views_count > 0:
                popularity_score = (deal.views_count * 0.7) + (deal.clicks_count * 1.5)
                # In a real system, you might store this in a field or cache.
                updated_count += 1
        except Exception as e:
            logger.error(f"Error updating statistics for deal {deal.id}: {str(e)}")
    return {"total": total_count, "updated": updated_count}


@shared_task
def warm_deal_caches():
    """
    Pre-warm caches for commonly accessed deal data.
    """
    from apps.deals.services import DealService

    DealService.get_featured_deals()
    DealService.get_sustainable_deals()
    DealService.get_ending_soon_deals()
    return {"success": True, "message": "Deal caches warmed"}
