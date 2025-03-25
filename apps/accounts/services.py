from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.crypto import get_random_string

from apps.categories.models import Category
from apps.deals.services import DealService
from core.utils.cache import cache_result, service_exception_handler
from core.utils.errors import ServiceError

User = get_user_model()


class UserService:
    """Service for user-related business logic, separating it from views
    and providing reusable methods for user management."""
    
    @staticmethod
    @cache_result(timeout=3600, prefix="user_profile")
    def get_user_profile(user_id):
        """Get a user's complete profile with related data"""
        try:
            user = User.objects.select_related('location').prefetch_related(
                'favorite_categories', 
                Prefetch('shops', queryset=User.objects.filter(is_active=True))
            ).get(id=user_id)
            
            return user
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")
    
    @staticmethod
    @cache_result(timeout=1800, prefix="user_email")
    def get_user_by_email(email):
        """Get a user by email with caching"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    @cache_result(timeout=3600, prefix="user_favorites")
    def get_favorite_categories(user_id):
        """Get a user's favorite categories with caching"""
        try:
            user = User.objects.get(id=user_id)
            return user.favorite_categories.all()
        except User.DoesNotExist:
            return []
    
    @staticmethod
    def toggle_favorite_category(user_id, category_id):
        """Toggle a category as favorite for a user"""
        try:
            user = User.objects.get(id=user_id)
            category = Category.objects.get(id=category_id)
            
            if category in user.favorite_categories.all():
                user.favorite_categories.remove(category)
                action = 'removed'
            else:
                user.favorite_categories.add(category)
                action = 'added'
            
            # Invalidate caches
            cache.delete(f"user_favorites:{user_id}")
            cache.delete(f"user_profile:{user_id}")
            
            return {'success': True, 'action': action}
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")
        except Category.DoesNotExist:
            raise ServiceError(f"Category with ID {category_id} not found", code="not_found")
    
    @staticmethod
    def get_personalized_deals(user_id, limit=10):
        """Get deals personalized to the user's preferences"""
        try:
            user = User.objects.get(id=user_id)
            favorite_categories = user.favorite_categories.all()
            
            if favorite_categories.exists():
                category_ids = [cat.id for cat in favorite_categories]
                return DealService.get_deals_by_multiple_categories(category_ids, limit)
            
            return DealService.get_featured_deals(limit)
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")
    
    @staticmethod
    def update_notification_preferences(user_id, preferences):
        """Update a user's notification preferences"""
        try:
            user = User.objects.get(id=user_id)
            
            current_prefs = user.notification_preferences or {}
            current_prefs.update(preferences)
            
            user.notification_preferences = current_prefs
            user.save(update_fields=['notification_preferences'])
            
            cache.delete(f"user_profile:{user_id}")
            
            return user.notification_preferences
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")
    
    @staticmethod
    def generate_password_reset_token(email):
        """Generate a password reset token for a user"""
        try:
            user = User.objects.get(email=email)
            token = get_random_string(length=32)
            
            return {
                'user_id': user.id,
                'token': token
            }
        except User.DoesNotExist:
            # For security reasons, don't reveal if the email exists
            return None
