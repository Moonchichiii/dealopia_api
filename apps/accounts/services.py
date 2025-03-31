import django.contrib.auth
import django.core.cache
import django.db.models
import django.utils.crypto

from apps.categories.models import Category
from apps.deals.services import DealService
from core.utils.cache import cache_result, service_exception_handler
from core.utils.errors import ServiceError

User = django.contrib.auth.get_user_model()


class UserService:
    """Service for user-related business logic"""

    @staticmethod
    @cache_result(timeout=3600, prefix="user_profile")
    def get_user_profile(user_id):
        """Get a user's complete profile with related data"""
        try:
            user = (
                User.objects.select_related("location")
                .prefetch_related(
                    "favorite_categories",
                    django.db.models.Prefetch("shops", queryset=User.objects.filter(is_active=True)),
                )
                .get(id=user_id)
            )
            return user
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")

    @staticmethod
    @cache_result(timeout=1800, prefix="user_email")
    def get_user_by_email(email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    @cache_result(timeout=3600, prefix="user_favorites")
    def get_favorite_categories(user_id):
        try:
            user = User.objects.get(id=user_id)
            return user.favorite_categories.all()
        except User.DoesNotExist:
            return []

    @staticmethod
    def _get_user_or_raise(user_id):
        """Helper to get user or raise consistent error"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")

    @staticmethod
    def _get_category_or_raise(category_id):
        """Helper to get category or raise consistent error"""
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise ServiceError(f"Category with ID {category_id} not found", code="not_found")

    @staticmethod
    def toggle_favorite_category(user_id, category_id):
        user = UserService._get_user_or_raise(user_id)
        category = UserService._get_category_or_raise(category_id)

        if category in user.favorite_categories.all():
            user.favorite_categories.remove(category)
            action = "removed"
        else:
            user.favorite_categories.add(category)
            action = "added"

        # Invalidate caches
        cache = django.core.cache.cache
        cache.delete(f"user_favorites:{user_id}")
        cache.delete(f"user_profile:{user_id}")

        return {"success": True, "action": action}

    @staticmethod
    def get_personalized_deals(user_id, limit=10):
        user = UserService._get_user_or_raise(user_id)
        favorite_categories = user.favorite_categories.all()

        if favorite_categories.exists():
            category_ids = [cat.id for cat in favorite_categories]
            return DealService.get_deals_by_multiple_categories(category_ids, limit)

        return DealService.get_featured_deals(limit)

    @staticmethod
    def update_notification_preferences(user_id, preferences):
        user = UserService._get_user_or_raise(user_id)

        current_prefs = user.notification_preferences or {}
        current_prefs.update(preferences)

        user.notification_preferences = current_prefs
        user.save(update_fields=["notification_preferences"])

        django.core.cache.cache.delete(f"user_profile:{user_id}")
        return user.notification_preferences

    @staticmethod
    def generate_password_reset_token(email):
        try:
            user = User.objects.get(email=email)
            token = django.utils.crypto.get_random_string(length=32)
            return {"user_id": user.id, "token": token}
        except User.DoesNotExist:
            # Security: don't reveal if email exists
            return None
