from django.db import models

class ScraperJob(models.Model):
    """Model to track and log website analysis jobs."""
    
    job_type = models.CharField(max_length=100, default="WebAnalysis")
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    sustainability_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Search Analysis Job"
        verbose_name_plural = "Search Analysis Jobs"
        
    def __str__(self):
        return f"{self.job_type} - {self.status} - {self.created_at.strftime('%Y-%m-%d')}"
        
    @property
    def duration(self):
        """Calculate the duration of the job."""
        if not self.completed_at:
            return None
        return self.completed_at - self.created_at