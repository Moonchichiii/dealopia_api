"""
Celery tasks for the deals app.
"""
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Union, Any

from celery import shared_task
from django.utils import timezone
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.accounts.models import User
from apps.scrapers.api_services import EcoRetailerAPI

logger = logging.getLogger(__name__)


@shared_task
def clean_expired_deals(days: int = 30) -> Dict[str, int]:
    """
    Remove deals that have been expired for more than the specified number of days.
    
    Args:
        days: Number of days after expiration to keep deals
        
    Returns:
        Dictionary with count of deleted deals
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Find deals that have been expired for longer than the cutoff
    expired_deals = Deal.objects.filter(
        end_date__lt=cutoff_date
    )
    
    count = expired_deals.count()
    expired_deals.delete()
    
    logger.info(f"Deleted {count} deals expired for more than {days} days")
    
    return {"deleted": count}


@shared_task
def import_deals_from_apis() -> Dict[str, Any]:
    """
    Task to import deals from all configured eco-friendly APIs.
   
    Returns:
        dict: Results dictionary containing counts of created/updated deals
              and any failed sources.
    """
    from apps.scrapers.services import DealImportService

    total_results = {"total_created": 0, "total_updated": 0, "failed_sources": []}

    # Get all the API sources we support
    api_sources = EcoRetailerAPI.SOURCES.keys()

    for source in api_sources:
        try:
            logger.info(f"Importing deals from {source}")
            result = DealImportService.import_from_source(source, limit=100)

            if result["success"]:
                total_results["total_created"] += result.get("created", 0)
                total_results["total_updated"] += result.get("updated", 0)
                logger.info(
                    f"Successfully imported from {source}: "
                    f"{result.get('created', 0)} created, "
                    f"{result.get('updated', 0)} updated"
                )
            else:
                total_results["failed_sources"].append(source)
                logger.error(
                    f"Failed to import from {source}: {result.get('error')}"
                )

        except Exception as e:
            total_results["failed_sources"].append(source)
            logger.exception(f"Error importing from {source}: {str(e)}")

    return total_results


@shared_task
def scrape_sustainable_deals() -> Dict[str, Any]:
    """
    Task to scrape deals from sustainable shopping sites.
    
    Returns:
        Dictionary with success status and results
    """
    try:
        from apps.deals.spiders.deal_spider import SustainableDealSpider
        
        # Configure Scrapy crawler
        process = CrawlerProcess(get_project_settings())
        
        # Add the spider to the process
        process.crawl(SustainableDealSpider)
        
        # Start the crawler process
        process.start()
        
        # Return success
        return {
            "success": True, 
            "message": "Scraping completed successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error running sustainable deals spider: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def update_sustainability_scores() -> Dict[str, int]:
    """
    Update sustainability scores for all deals.
    
    Returns:
        Dictionary with counts of updates and errors
    """
    deals = Deal.objects.all()
    updated = 0
    errors = 0
    
    for deal in deals:
        try:
            deal.calculate_sustainability_score()
            updated += 1
        except Exception as e:
            logger.error(f"Error updating sustainability score for deal {deal.id}: {str(e)}")
            errors += 1
    
    return {
        "updated": updated,
        "errors": errors,
        "total": updated + errors
    }


@shared_task
def send_deal_notifications(deal_id: int) -> Dict[str, Any]:
    """
    Send notifications for a newly created or updated deal.
    
    Args:
        deal_id: ID of the deal to send notifications for
        
    Returns:
        Dictionary with success status
    """
    try:
        deal = Deal.objects.get(id=deal_id)
        
        # Find users who should receive notifications about this deal
        # This could be based on user preferences, location, etc.
        relevant_users = User.objects.filter(
            # Users who have favorited relevant categories
            favorite_categories__in=deal.categories.all()
        ).distinct()
        
        if not relevant_users.exists():
            logger.info(f"No users to notify about deal {deal.id}: {deal.title}")
            return {
                "success": True,
                "deal_id": deal_id,
                "notifications_sent": 0
            }
        
        # In a real implementation, this would send emails, push notifications, etc.
        logger.info(f"Would notify {relevant_users.count()} users about new deal: {deal.title}")
        
        return {
            "success": True,
            "deal_id": deal_id,
            "notifications_sent": relevant_users.count()
        }
        
    except Deal.DoesNotExist:
        logger.error(f"Deal {deal_id} not found - cannot send notifications")
        return {
            "success": False,
            "error": f"Deal {deal_id} not found"
        }
    except Exception as e:
        logger.error(f"Error sending notifications for deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }