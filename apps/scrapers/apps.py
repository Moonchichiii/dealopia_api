from django.apps import AppConfig

class ScrapersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scrapers'
    verbose_name = 'Web Scrapers'
    
    def ready(self):
        import apps.scrapers.signals
