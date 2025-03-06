from django.db.models import F, Q
from django.utils import timezone
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point

from .models import Deal
from apps.locations.models import Location
from apps.categories.models import Category


class DealService:
    """
    Service for deal-related business logic, separating it from views
    and providing reusable methods for deals management.
    """
    
    @staticmethod
    def get_active_deals(queryset=None):
        """Return only currently active deals (not expired)"""
        queryset = queryset or Deal.objects.all()
        now = timezone.now()
        return queryset.filter(
            start_date__lte=now,
            end_date__gte=now,
            is_verified=True
        )
    
    @staticmethod
    def get_featured_deals(limit=6):
        """Get featured deals for homepage"""
        return DealService.get_active_deals().filter(
            is_featured=True
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_expiring_soon_deals(days=3, limit=6):
        """Get deals that are expiring within the specified number of days"""
        now = timezone.now()
        threshold = now + timezone.timedelta(days=days)
        
        return DealService.get_active_deals().filter(
            end_date__lte=threshold
        ).order_by('end_date')[:limit]
    
    @staticmethod
    def get_new_deals(days=7, limit=6):
        """Get deals that were created within the specified number of days"""
        threshold = timezone.now() - timezone.timedelta(days=days)
        
        return DealService.get_active_deals().filter(
            created_at__gte=threshold
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def search_deals(search_query, category_id=None):
        """Search deals by title, description, and optionally filter by category"""
        queryset = DealService.get_active_deals()
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(shop__name__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()
        
        if category_id:
            # Include subcategories in the filter
            category_ids = [category_id]
            try:
                category = Category.objects.get(id=category_id)
                category_ids.extend(category.children.values_list('id', flat=True))
            except Category.DoesNotExist:
                pass
                
            queryset = queryset.filter(categories__id__in=category_ids)
        
        return queryset
    
    @staticmethod
    def get_deals_by_location(latitude, longitude, radius_km=10):
        """Get deals near a specific location using geodjango"""
        user_location = Point(longitude, latitude, srid=4326)
        
        # First find shops near the location
        nearby_locations = Location.objects.filter(
            point__distance_lte=(user_location, D(km=radius_km))
        )
        
        # Then get deals from those shops
        return DealService.get_active_deals().filter(
            shop__location__in=nearby_locations
        ).order_by('shop__location__point__distance_to'(user_location))
    
    @staticmethod
    def record_view(deal_id):
        """Increment the view count for a deal"""
        Deal.objects.filter(id=deal_id).update(views_count=F('views_count') + 1)
    
    @staticmethod
    def record_click(deal_id):
        """Increment the click count for a deal"""
        Deal.objects.filter(id=deal_id).update(clicks_count=F('clicks_count') + 1)
        
    @staticmethod
    def get_related_deals(deal, limit=3):
        """Get related deals based on category and excluding the current deal"""
        category_ids = deal.categories.values_list('id', flat=True)
        
        related_deals = DealService.get_active_deals().filter(
            categories__id__in=category_ids
        ).exclude(id=deal.id).distinct()
        
        # If we have deals from the same shop, prioritize those
        same_shop_deals = related_deals.filter(shop=deal.shop)
        
        if same_shop_deals.count() >= limit:
            return same_shop_deals.order_by('-is_featured', '-created_at')[:limit]
        
        # Otherwise, mix them with other related deals
        same_shop_count = min(same_shop_deals.count(), limit // 2)
        other_deals_count = limit - same_shop_count
        
        result = list(same_shop_deals.order_by('-is_featured', '-created_at')[:same_shop_count])
        result.extend(
            related_deals.exclude(shop=deal.shop)
            .order_by('-is_featured', '-created_at')[:other_deals_count]
        )
        
        return result