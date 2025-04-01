"""
Application configuration for the scrapers app.
"""
from django.apps import AppConfig


class ScrapersConfig(AppConfig):
    """Configuration for the scrapers app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scrapers'
    verbose_name = 'Web Scrapers'
    
    def ready(self):
        """
        Initialize app when Django starts.
        Import signals to activate them.
        """
        # Import signals
        import apps.scrapers.signals