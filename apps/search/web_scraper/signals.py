import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.search.web_scraper.models import ScraperJob

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ScraperJob)
def log_scraper_job(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Scraper job {instance.id} created for {instance.spider_name}")
    else:
        logger.info(f"Scraper job {instance.id} updated: status={instance.status}")
