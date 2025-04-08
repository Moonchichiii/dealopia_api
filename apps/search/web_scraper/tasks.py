import logging
from typing import Dict, Any

from celery import shared_task
from django.utils import timezone

from apps.search.models import ScraperJob
from apps.search.web_scraper.services import WebScraperService

logger = logging.getLogger("dealopia.search")

@shared_task
def analyze_website(url: str) -> Dict[str, Any]:
    """Analyze a website for sustainability information."""
    job = ScraperJob.objects.create(
        job_type="WebAnalysis",
        status="running",
        source_url=url
    )
    
    try:
        result = WebScraperService.analyze_shop_website(url)
        
        job.status = "completed"
        job.completed_at = timezone.now()
        
        if "error" in result:
            job.status = "failed"
            job.error_message = result["error"]
        else:
            job.sustainability_score = result.get("sustainability", {}).get("score", 0)
            
        job.save()
        
        return {
            "success": True,
            "url": url,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing website {url}: {e}")
        
        job.status = "failed"
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.save()
        
        return {
            "success": False,
            "error": str(e),
            "url": url
        }
