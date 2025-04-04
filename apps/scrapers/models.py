"""
Models for the scrapers app.
"""
from django.db import models

class ScraperJob(models.Model):
    spider_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    items_scraped = models.IntegerField(default=0)
    deals_created = models.IntegerField(default=0)
    deals_updated = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Scraper Job"
        verbose_name_plural = "Scraper Jobs"

    def __str__(self):
        return f"{self.spider_name} - {self.status}"

    
    @property
    def duration(self):
        """Calculate the duration of the job."""
        if not self.completed_at:
            return None
        
        return self.completed_at - self.created_at
    
    @property
    def success_rate(self):
        """Calculate the success rate of the job."""
        if self.items_scraped == 0:
            return 0
        
        return (1 - (self.error_count / self.items_scraped)) * 100