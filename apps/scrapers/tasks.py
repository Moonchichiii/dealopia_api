"""
Celery tasks for the scrapers app.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from playwright.sync_api import sync_playwright

from apps.deals.models import Deal
from apps.shops.models import Shop
from .models import ScraperJob
from .services import ScraperService, DealImportService, CrawlbaseAPIService

logger = logging.getLogger("dealopia.scrapers")


@shared_task(bind=True, max_retries=3)
def scrape_shop(self, shop_id: int) -> Dict[str, Any]:
    """
    Scrape deals from a shop's website.
    
    Args:
        shop_id: ID of the shop to scrape
        
    Returns:
        Dictionary with results of the scraping operation
    """
    # Create a scraper job record
    job = ScraperJob.objects.create(
        spider_name="ShopScraper",
        status="running",
        source_url=Shop.objects.get(id=shop_id).website or ""
    )
    
    try:
        # Perform the scraping
        result = ScraperService.scrape_shop_deals(shop_id)
        
        # Update the job with the results
        job.status = "completed" if result["success"] else "failed"
        job.completed_at = timezone.now()
        job.items_scraped = result.get("total_processed", 0)
        job.deals_created = result.get("deals_created", 0)
        job.deals_updated = result.get("deals_updated", 0)
        
        if not result["success"]:
            job.error_message = result.get("error", "Unknown error")
            job.error_count = 1
            
        job.save()
        
        return result
        
    except Exception as e:
        # Mark job as failed
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.error_count = 1
        job.save()
        
        # Retry the task
        self.retry(exc=e, countdown=60 * self.request.retries)
        
        return {
            "success": False,
            "error": str(e)
        }


@shared_task(bind=True)
def import_deals_from_api(self, source_name: str, limit: int = 100) -> Dict[str, Any]:
    """
    Import deals from a specific API source.
    
    Args:
        source_name: Name of the source to import from
        limit: Maximum number of deals to import
        
    Returns:
        Dictionary with results of the import operation
    """
    # Create job record
    job = ScraperJob.objects.create(
        spider_name=f"API-{source_name}",
        status="running"
    )
    
    try:
        # Perform the import
        result = DealImportService.import_from_source(source_name, limit)
        
        # Update the job with the results
        job.status = "completed" if result["success"] else "failed"
        job.completed_at = timezone.now()
        job.deals_created = result.get("created", 0)
        job.deals_updated = result.get("updated", 0)
        
        if not result["success"]:
            job.error_message = result.get("error", "Unknown error")
            job.error_count = 1
            
        job.save()
        
        return result
        
    except Exception as e:
        # Mark job as failed
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.error_count = 1
        job.save()
        
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def scrape_and_import_using_crawlbase(shop_id: int, scrape_url: str, use_js: bool = True) -> Dict[str, Any]:
    """
    Scrape and import deals using Crawlbase API.
    
    Args:
        shop_id: ID of the shop to associate deals with
        scrape_url: URL to scrape for deals
        use_js: Whether to use JavaScript rendering
        
    Returns:
        Dictionary with results of the operation
    """
    # Create job record
    job = ScraperJob.objects.create(
        spider_name="Crawlbase",
        status="running",
        source_url=scrape_url
    )
    
    try:
        # Perform the scrape and import
        result = CrawlbaseAPIService.scrape_and_import_deals(shop_id, scrape_url, use_js)
        
        # Update the job with the results
        job.status = "completed" if result["success"] else "failed"
        job.completed_at = timezone.now()
        job.items_scraped = result.get("total_processed", 0)
        job.deals_created = result.get("deals_created", 0)
        job.deals_updated = result.get("deals_updated", 0)
        
        if not result["success"]:
            job.error_message = result.get("error", "Unknown error")
            job.error_count = 1
            
        job.save()
        
        return result
        
    except Exception as e:
        # Mark job as failed
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.error_count = 1
        job.save()
        
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def bulk_scrape_shops(shop_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Scrape deals from multiple shops in bulk.
    
    Args:
        shop_ids: List of shop IDs to scrape, or None to scrape all verified shops
        
    Returns:
        Dictionary with aggregated results
    """
    if shop_ids is None:
        # Get all verified shops with websites
        shop_ids = list(Shop.objects.filter(
            is_verified=True, 
            website__isnull=False
        ).values_list('id', flat=True))
    
    results = {
        "total_shops": len(shop_ids),
        "successful": 0,
        "failed": 0,
        "total_deals_created": 0,
        "total_deals_updated": 0
    }
    
    for shop_id in shop_ids:
        try:
            # Queue the task for each shop
            scrape_shop.delay(shop_id)
            results["successful"] += 1
        except Exception as e:
            logger.error(f"Error queueing scrape task for shop {shop_id}: {str(e)}")
            results["failed"] += 1
    
    return results