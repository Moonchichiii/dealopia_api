from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import models
from django.db.models import F, Q, Count, Prefetch
from django.utils import timezone

from apps.categories.models import Category
from core.utils.cache import cache_result
from .models import Deal


class DealService:
    """
    Service for deal-related business logic, separating it from views
    and providing reusable methods for deals management.
    """
    
    @staticmethod
    def get_active_deals(queryset=None):
        """
        Return only currently active deals (not expired).
        
        Optimizes query performance by default with select_related for Shop
        and prefetch_related for Categories.
        """
        queryset = queryset or Deal.objects.all()
        now = timezone.now()
        
        return (
            queryset
            .filter(
                start_date__lte=now,
                end_date__gte=now,
                is_verified=True
            )
            .select_related('shop')
            .prefetch_related('categories')
        )
    
    @staticmethod
    @cache_result(timeout=1800, prefix="featured_deals")
    def get_featured_deals(limit=6):
        """Get featured deals for homepage."""
        return (
            DealService.get_active_deals()
            .filter(is_featured=True)
            .order_by('-created_at')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=3600, prefix="expiring_deals")
    def get_expiring_soon_deals(days=3, limit=6):
        """Get deals that are expiring within the specified number of days."""
        now = timezone.now()
        threshold = now + timezone.timedelta(days=days)
        
        return (
            DealService.get_active_deals()
            .filter(end_date__lte=threshold)
            .order_by('end_date')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=3600, prefix="new_deals")
    def get_new_deals(days=7, limit=6):
        """Get deals that were created within the specified number of days."""
        threshold = timezone.now() - timezone.timedelta(days=days)
        
        return (
            DealService.get_active_deals()
            .filter(created_at__gte=threshold)
            .order_by('-created_at')[:limit]
        )
    
    @staticmethod
    def search_deals(search_query, category_id=None):
        """Search deals by title, description, and optionally filter by category."""
        queryset = DealService.get_active_deals()
        
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
                # Include child categories
                category_ids.extend(category.children.values_list('id', flat=True))
            except Category.DoesNotExist:
                pass
                
            queryset = queryset.filter(categories__id__in=category_ids)
        
        return queryset
    
    @staticmethod
    @cache_result(timeout=3600, prefix="category")
    def get_deals_by_category(category_id, limit=12):
        """Get deals by category, including child categories."""
        category_ids = [category_id]
        
        try:
            category = Category.objects.get(id=category_id)
            # Include child categories
            category_ids.extend(category.children.values_list('id', flat=True))
        except Category.DoesNotExist:
            pass
            
        return (
            DealService.get_active_deals()
            .filter(categories__id__in=category_ids)
            .distinct()
            .order_by('-is_featured', '-created_at')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=1800, prefix="nearby_deals")
    def get_deals_by_location(latitude, longitude, radius_km=10):
        """Get deals near a specific location using geodjango."""
        user_location = Point(longitude, latitude, srid=4326)
        radius_km = min(max(0.1, radius_km), 50)  # Between 100m and 50km
        
        return (
            DealService.get_active_deals()
            .filter(
                shop__location__point__distance_lte=(user_location, D(km=radius_km))
            )
            .annotate(
                distance=Distance('shop__location__point', user_location)
            )
            .order_by('distance')
        )
    
    @staticmethod
    def record_view(deal_id):
        """Increment the view count for a deal."""
        Deal.objects.filter(id=deal_id).update(views_count=F('views_count') + 1)
    
    @staticmethod
    def record_click(deal_id):
        """Increment the click count for a deal."""
        Deal.objects.filter(id=deal_id).update(clicks_count=F('clicks_count') + 1)
    
    @staticmethod
    @cache_result(timeout=1800, prefix="related_deals")
    def get_related_deals(deal, limit=3):
        """Get related deals based on category and excluding the current deal."""
        if isinstance(deal, int):
            try:
                deal = Deal.objects.get(id=deal)
            except Deal.DoesNotExist:
                return []
        
        category_ids = list(deal.categories.values_list('id', flat=True))
        
        if not category_ids:
            return []
        
        # First get deals from same shop and categories
        same_shop_deals = (
            DealService.get_active_deals()
            .filter(
                shop=deal.shop,
                categories__id__in=category_ids
            )
            .exclude(id=deal.id)
            .distinct()
        )
        
        # Calculate how many same-shop deals to include
        same_shop_count = min(same_shop_deals.count(), limit // 2)
        result = list(same_shop_deals.order_by('-is_featured', '-created_at')[:same_shop_count])
        
        # Fill remaining slots with other shop deals
        needed_count = limit - len(result)
        if needed_count > 0:
            other_deals = (
                DealService.get_active_deals()
                .filter(categories__id__in=category_ids)
                .exclude(id=deal.id)
                .exclude(shop=deal.shop)
                .distinct()
                .order_by('-is_featured', '-created_at')[:needed_count]
            )
            
            result.extend(other_deals)
        
        return result
    
    @staticmethod
    @cache_result(timeout=86400, prefix="popular_deals")
    def get_popular_deals(limit=6):
        """Get most viewed/clicked deals."""
        return (
            DealService.get_active_deals()
            .order_by('-views_count', '-clicks_count')[:limit]
        )
        
    @staticmethod
    @cache_result(timeout=1800, prefix="multi_category")
    def get_deals_by_multiple_categories(category_ids, limit=12):
        """Get deals that match any of the provided categories."""
        if not category_ids:
            return []
        
        all_category_ids = list(category_ids)
        
        # Include child categories
        child_categories = Category.objects.filter(parent_id__in=category_ids)
        all_category_ids.extend(child_categories.values_list('id', flat=True))
        
        return (
            DealService.get_active_deals()
            .filter(categories__id__in=all_category_ids)
            .distinct()
            .order_by('-is_featured', '-created_at')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=3600, prefix="sustainable_deals")
    def get_sustainable_deals(limit=10):
        """Get deals from sustainable brands and categories."""
        sustainable_categories = Category.objects.filter(
            Q(name__icontains='sustain') | Q(is_eco_friendly=True)
        ).values_list('id', flat=True)
        
        if not sustainable_categories:
            return DealService.get_featured_deals(limit)
        
        return (
            DealService.get_active_deals()
            .filter(categories__id__in=sustainable_categories)
            .distinct()
            .order_by('-is_featured', '-created_at')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=1800, prefix="deals_by_price")
    def get_deals_by_price_range(min_price=None, max_price=None, limit=12):
        """Get deals within a specific price range."""
        queryset = DealService.get_active_deals()
        
        if min_price is not None:
            queryset = queryset.filter(discounted_price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(discounted_price__lte=max_price)
        
        return queryset.order_by('-is_featured', '-created_at')[:limit]
    
    @staticmethod
    @cache_result(timeout=1800, prefix="deals_by_discount")
    def get_deals_by_minimum_discount(min_discount_percentage=20, limit=12):
        """Get deals with a minimum discount percentage."""
        return (
            DealService.get_active_deals()
            .filter(discount_percentage__gte=min_discount_percentage)
            .order_by('-discount_percentage')[:limit]
        )
    
    @staticmethod
    @cache_result(timeout=3600, prefix="trending_deals")
    def get_trending_deals(days=7, limit=10):
        """Get trending deals based on views and clicks in the last X days."""
        threshold_date = timezone.now() - timezone.timedelta(days=days)
        
        return (
            DealService.get_active_deals()
            .filter(created_at__gte=threshold_date)
            .annotate(
                score=F('views_count') + (F('clicks_count') * 3)
            )
            .filter(score__gt=0)
            .order_by('-score')[:limit]
        )