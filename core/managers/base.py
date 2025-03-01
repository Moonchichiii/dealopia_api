from django.db import models

class BaseQuerySet(models.QuerySet):
    """Base queryset with common functionality"""
    
    def active(self):
        """Filter for active objects"""
        return self.filter(is_active=True)
    
    def featured(self):
        """Filter for featured objects"""
        return self.filter(is_featured=True)
    
    def recent(self):
        """Order by recently created"""
        return self.order_by('-created_at')

class BaseManager(models.Manager):
    """Base manager that uses the BaseQuerySet"""
    
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def featured(self):
        return self.get_queryset().featured()
    
    def recent(self):
        return self.get_queryset().recent()
