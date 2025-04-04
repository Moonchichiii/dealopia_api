"""
Signal handlers for the scrapers app.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

#from .scrapers import capture_exception, clean_deal_data
#from .models import ScraperJob, ScrapedDeal, ScraperProxy  # Ensure these models exist

#@receiver(post_save, sender=ScrapedDeal)
#def clean_deal_on_save(sender, instance, created, **kwargs):
#    """
#    Clean and validate deal data when a new deal is saved.
#    """
#    if created:
#        try:
#            # Ensure that instance.to_dict() and instance.is_valid exist.
#            cleaned_data = clean_deal_data([instance.to_dict()])
#            if not cleaned_data:
#                instance.is_valid = False
#                instance.save(update_fields=['is_valid'])
#                logger.info(f"ScrapedDeal {instance.id} marked as invalid after cleaning.")
#        except Exception as e:
#            capture_exception(e)
#            logger.exception(f"Error cleaning ScrapedDeal {instance.id}: {e}")

#@receiver(post_save, sender=ScraperJob)
#def log_scraper_job(sender, instance, created, **kwargs):
#    """
#    Log when scraper jobs are created or updated.
#    """
#    if created:
#        logger.info(f"Scraper job {instance.id} created for {instance.spider_name}")
#    else:
#        logger.info(f"Scraper job {instance.id} updated: status={instance.status}")

#@receiver(pre_delete, sender=ScraperProxy)
#def cleanup_failed_proxies(sender, instance, **kwargs):
#    """
#    Perform cleanup when a proxy is removed from rotation.
#    Clean up any cached proxy information.
#    """
#    from django.core.cache import cache
#    cache_key = f"proxy_{instance.ip_address}"
#    cache.delete(cache_key)
#    
#    logger.info(f"Proxy {instance.ip_address}:{instance.port} removed from rotation")
#    
    # Mark any active scraper jobs using this proxy as failed.
#    active_jobs = ScraperJob.objects.filter(
#        proxy=instance,
#        status__in=['pending', 'running']
#    )
#    for job in active_jobs:
#        job.status = 'failed'
#        job.error_message = "Proxy removed from rotation"
#        job.save(update_fields=['status', 'error_message'])
#        logger.info(f"Scraper job {job.id} marked as failed due to proxy removal.")
