import logging

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.deals.models import Deal
from apps.shops.models import Shop

logger = logging.getLogger("dealopia.tasks")


@shared_task
def import_deals_from_apis():
    """Task to import deals from all configured eco-friendly APIs."""
    from apps.deals.services import DealImportService

    total_results = {"total_created": 0, "total_updated": 0, "failed_sources": []}

    # Get all the API sources we support
    from apps.deals.services import EcoRetailerAPI

    api_sources = EcoRetailerAPI.SOURCES.keys()

    for source in api_sources:
        try:
            logger.info(f"Importing deals from {source}")
            result = DealImportService.import_from_source(source, limit=100)

            if result["success"]:
                total_results["total_created"] += result.get("created", 0)
                total_results["total_updated"] += result.get("updated", 0)
                logger.info(
                    f"Successfully imported from {source}: {result.get('created', 0)} created, {result.get('updated', 0)} updated"
                )
            else:
                total_results["failed_sources"].append(source)
                logger.error(f"Failed to import from {source}: {result.get('error')}")

        except Exception as e:
            total_results["failed_sources"].append(source)
            logger.exception(f"Error importing from {source}: {str(e)}")

    return total_results


@shared_task
def scrape_sustainable_deals():
    """Task to scrape deals from configured shops."""
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    from apps.deals.spiders.sustainable_deal_spider import \
        SustainableDealSpider

    try:
        process = CrawlerProcess(get_project_settings())
        process.crawl(SustainableDealSpider)
        process.start()  # Blocks until crawling is finished

        return {"success": True, "message": "Scraping completed successfully"}
    except Exception as e:
        logger.exception(f"Error during scraping: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def update_sustainability_scores():
    """Update sustainability scores for all active deals."""
    updated_count = 0
    error_count = 0

    # Get active deals without a good sustainability score
    deals = Deal.get_active().filter(
        Q(sustainability_score__lt=7.0) | Q(sustainability_score__isnull=True)
    )

    logger.info(f"Updating sustainability scores for {deals.count()} deals")

    for deal in deals.iterator(chunk_size=100):
        try:
            deal.calculate_sustainability_score()
            updated_count += 1
        except Exception as e:
            error_count += 1
            logger.error(
                f"Error updating sustainability score for deal {deal.id}: {str(e)}"
            )

    return {
        "updated": updated_count,
        "errors": error_count,
        "total": updated_count + error_count,
    }


@shared_task
def clean_expired_deals(days=30):
    """Clean up expired deals older than the specified days."""
    cutoff_date = timezone.now() - timezone.timedelta(days=days)

    expired_deals = Deal.objects.filter(end_date__lt=cutoff_date)

    count = expired_deals.count()
    expired_deals.delete()

    logger.info(f"Deleted {count} expired deals older than {days} days")

    return {"deleted": count}


@shared_task
def send_deal_notifications(deal_id):
    """Send notifications to users about a new deal.

    Notifies users who have subscribed to deal categories or shops,
    or who are in the vicinity of the deal's location.

    Args:
        deal_id (int): The ID of the newly created deal

    Returns:
        dict: Results of the notification process
    """
    from apps.deals.models import Deal

    try:
        deal = (
            Deal.objects.select_related("shop")
            .prefetch_related("categories")
            .get(id=deal_id)
        )

        logger.info(f"Sending notifications for new deal: {deal.title} (ID: {deal_id})")

        # Example notification logic - implement based on your notification system
        # notify_users_by_category(deal)
        # notify_users_by_shop(deal)
        # notify_nearby_users(deal)

        # For now, just log that we would send notifications
        logger.info(f"Would notify users about: {deal.title} at {deal.shop.name}")

        return {
            "success": True,
            "deal_id": deal_id,
            "notifications_sent": 0,  # Update with actual count when implemented
        }

    except Deal.DoesNotExist:
        logger.error(f"Cannot send notifications: Deal {deal_id} not found")
        return {"success": False, "error": f"Deal {deal_id} not found"}
    except Exception as e:
        logger.exception(f"Error sending notifications for deal {deal_id}: {str(e)}")
        return {"success": False, "error": str(e)}
