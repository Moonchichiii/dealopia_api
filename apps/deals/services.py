from django.db.models import F, Q, Count, Prefetch
from django.utils import timezone
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from .models import Deal
from apps.locations.models import Location
from apps.categories.models import Category
from core.utils.cache import cache_result


class DealService:
    """
    Service for deal-related business logic, separating it from views
    and providing reusable methods for deals management.
    """
    
    @staticmethod
    def get_active_deals(queryset=None, prefetch_related_fields=None, select_related_fields=None):
        """Return only currently active deals (not expired)"""
        queryset = queryset or Deal.objects.all()
        now = timezone.now()
        
        queryset = queryset.filter(
            start_date__lte=now,
            end_date__gte=now,
            is_verified=True
        )
        
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
            
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
            
        return queryset
    
    @staticmethod
    @cache_result(timeout=1800, prefix="featured_deals")  # 30 minute cache
    def get_featured_deals(limit=6):
        """Get featured deals for homepage"""
        return DealService.get_active_deals(
            select_related_fields=['shop'],
            prefetch_related_fields=['categories']
        ).filter(
            is_featured=True
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    @cache_result(timeout=3600, prefix="expiring_deals")  # 1 hour cache
    def get_expiring_soon_deals(days=3, limit=6):
        """Get deals that are expiring within the specified number of days"""
        now = timezone.now()
        threshold = now + timezone.timedelta(days=days)
        
        return DealService.get_active_deals(
            select_related_fields=['shop']
        ).filter(
            end_date__lte=threshold
        ).order_by('end_date')[:limit]
    
    @staticmethod
    @cache_result(timeout=3600, prefix="new_deals")  # 1 hour cache
    def get_new_deals(days=7, limit=6):
        """Get deals that were created within the specified number of days"""
        threshold = timezone.now() - timezone.timedelta(days=days)
        
        return DealService.get_active_deals(
            select_related_fields=['shop']
        ).filter(
            created_at__gte=threshold
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def search_deals(search_query, category_id=None):
        """Search deals by title, description, and optionally filter by category"""
        queryset = DealService.get_active_deals(
            select_related_fields=['shop'],
            prefetch_related_fields=['categories']
        )
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(shop__name__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()
        
        if category_id:
            category_ids = [category_id]
            try:
                category = Category.objects.get(id=category_id)
                category_ids.extend(category.children.values_list('id', flat=True))
            except Category.DoesNotExist:
                pass
                
            queryset = queryset.filter(categories__id__in=category_ids)
        
        return queryset
    
    @staticmethod
    @cache_result(timeout=3600, prefix="category")
    def get_deals_by_category(category_id, limit=12):
        """Get deals by category, including child categories"""
        category_ids = [category_id]
        
        try:
            category = Category.objects.get(id=category_id)
            category_ids.extend(category.children.values_list('id', flat=True))
        except Category.DoesNotExist:
            pass
            
        return DealService.get_active_deals(
            select_related_fields=['shop']
        ).filter(
            categories__id__in=category_ids
        ).distinct().order_by('-is_featured', '-created_at')[:limit]
    
    @staticmethod
    @cache_result(timeout=300, prefix="nearby_deals")  # 5 minute cache
    def get_deals_by_location(latitude, longitude, radius_km=10):
        """Get deals near a specific location using geodjango"""
        user_location = Point(longitude, latitude, srid=4326)
        
        return DealService.get_active_deals(
            select_related_fields=['shop', 'shop__location']
        ).filter(
            shop__location__point__distance_lte=(user_location, D(km=radius_km))
        ).annotate(
            distance=Distance('shop__location__point', user_location)
        ).order_by('distance')
    
    @staticmethod
    def record_view(deal_id):
        """Increment the view count for a deal"""
        Deal.objects.filter(id=deal_id).update(views_count=F('views_count') + 1)
    
    @staticmethod
    def record_click(deal_id):
        """Increment the click count for a deal"""
        Deal.objects.filter(id=deal_id).update(clicks_count=F('clicks_count') + 1)
        
    @staticmethod
    @cache_result(timeout=1800, prefix="related_deals")
    def get_related_deals(deal_id, limit=3):
        """Get related deals based on category and excluding the current deal"""
        deal = Deal.objects.get(id=deal_id)
        category_ids = deal.categories.values_list('id', flat=True)
        
        related_deals = DealService.get_active_deals(
            select_related_fields=['shop']
        ).filter(
            categories__id__in=category_ids
        ).exclude(id=deal.id).distinct()
        
        same_shop_deals = related_deals.filter(shop=deal.shop)
        
        if same_shop_deals.count() >= limit:
            return same_shop_deals.order_by('-is_featured', '-created_at')[:limit]
        
        same_shop_count = min(same_shop_deals.count(), limit // 2)
        other_deals_count = limit - same_shop_count
        
        result = list(same_shop_deals.order_by('-is_featured', '-created_at')[:same_shop_count])
        result.extend(
            related_deals.exclude(shop=deal.shop)
            .order_by('-is_featured', '-created_at')[:other_deals_count]
        )
        
        return result
    
    @staticmethod
    @cache_result(timeout=86400, prefix="popular_deals")
    def get_popular_deals(limit=6):
        """Get most viewed/clicked deals"""
        return DealService.get_active_deals(
            select_related_fields=['shop']
        ).order_by('-views_count', '-clicks_count')[:limit]