from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Avg, Count, F, Q

from apps.deals.models import Deal
from apps.locations.models import Location
from .models import Shop


class ShopService:
    """Service for shop-related business logic, separating it from views."""
    
    @staticmethod
    def get_verified_shops(queryset=None):
        """Return only verified shops"""
        queryset = queryset or Shop.objects.all()
        return queryset.filter(is_verified=True)
    
    @staticmethod
    def get_featured_shops(limit=4):
        """Get featured shops for homepage"""
        return ShopService.get_verified_shops().filter(
            is_featured=True
        ).order_by('-rating')[:limit]
    
    @staticmethod
    def get_popular_shops(limit=6):
        """Get popular shops based on deal count and rating"""
        return ShopService.get_verified_shops().annotate(
            active_deal_count=Count(
                'deals', 
                filter=Q(deals__is_verified=True)
            )
        ).filter(
            active_deal_count__gt=0
        ).order_by('-active_deal_count', '-rating')[:limit]
    
    @staticmethod
    def search_shops(search_query, category_id=None):
        """Search shops by name, description, and filter by category"""
        queryset = ShopService.get_verified_shops()
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()
        
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        return queryset
    
    @staticmethod
    def get_shops_by_location(latitude, longitude, radius_km=10):
        """Get shops near a specific location using geodjango"""
        user_location = Point(longitude, latitude, srid=4326)
        
        nearby_locations = Location.objects.filter(
            point__distance_lte=(user_location, D(km=radius_km))
        )
        
        return ShopService.get_verified_shops().filter(
            location__in=nearby_locations
        ).annotate(
            distance=F('location__point__distance_to')(user_location)
        ).order_by('distance')
    
    @staticmethod
    def get_shop_with_deals(shop_id):
        """Get shop details with active deals"""
        shop = Shop.objects.get(id=shop_id)
        
        # Import here to avoid circular imports
        from apps.deals.services import DealService
        active_deals = DealService.get_active_deals().filter(shop=shop)
        
        return {
            'shop': shop,
            'deals': active_deals
        }
    
    @staticmethod
    def calculate_shop_rating(shop_id):
        """Recalculate shop rating based on user reviews"""
        from apps.reviews.models import Review
        
        avg_rating = Review.objects.filter(
            shop_id=shop_id, 
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        avg_rating = round(avg_rating, 1)
        Shop.objects.filter(id=shop_id).update(rating=avg_rating)
        return avg_rating
    
    @staticmethod
    def get_shops_with_deals_in_category(category_id, limit=6):
        """Get shops that have active deals in a specific category"""
        return ShopService.get_verified_shops().filter(
            deals__categories__id=category_id,
            deals__is_verified=True
        ).annotate(
            category_deal_count=Count(
                'deals', 
                filter=Q(
                    deals__categories__id=category_id,
                    deals__is_verified=True
                )
            )
        ).filter(
            category_deal_count__gt=0
        ).order_by('-category_deal_count')[:limit]
