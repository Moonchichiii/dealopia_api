from django.db import models


class ScraperJob(models.Model):
    """Model representing a web scraper job execution."""
    
    spider_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scraper Job'
        verbose_name_plural = 'Scraper Jobs'
    
    def __str__(self):
        return f"{self.spider_name} - {self.status}"


class ScrapedDeal(models.Model):
    """Model representing a deal that was scraped from a website."""
    
    job = models.ForeignKey(
        ScraperJob, 
        on_delete=models.CASCADE, 
        related_name='deals'
    )
    title = models.CharField(max_length=255)
    url = models.URLField()
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Scraped Deal'
        verbose_name_plural = 'Scraped Deals'
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'title': self.title,
            'url': self.url,
        }
    
    def __str__(self):
        return self.title


class ScraperProxy(models.Model):
    """Model representing a proxy server for scrapers."""
    
    host = models.CharField(max_length=100)
    port = models.IntegerField()
    is_active = models.BooleanField(default=True)
    failure_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Scraper Proxy'
        verbose_name_plural = 'Scraper Proxies'
        unique_together = ['host', 'port']
    
    def __str__(self):
        return f"{self.host}:{self.port}"