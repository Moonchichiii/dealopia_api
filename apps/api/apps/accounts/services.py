from __future__ import annotations

import django.db.models
from typing import Any, Dict, Optional, Union

# Third-party imports
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.crypto import get_random_string
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework_simplejwt.tokens import RefreshToken

# Local application imports
from apps.categories.models import Category
from apps.deals.services import DealService
from apps.shops.models import Shop
from core.utils.cache import cache_result
from core.utils.errors import ServiceError

User = get_user_model()


class AuthService:
    """Service for authentication-related operations."""

    @staticmethod
    def issue_tokens_for_user(user: User) -> Dict[str, str]:
        """Generate and return tokens for a user."""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def verify_two_factor(user_id: int, token: str) -> Union[Dict[str, str], bool]:
        """Verify a 2FA token."""
        try:
            user = User.objects.get(id=user_id)
            # Assuming only one TOTP device per user for simplicity
            device = TOTPDevice.objects.get(user=user, confirmed=True)
            if device.verify_token(token):
                return AuthService.issue_tokens_for_user(user)
            return False
        except (User.DoesNotExist, TOTPDevice.DoesNotExist):
            return False


class UserService:
    """Service for user-related business logic."""

    @staticmethod
    @cache_result(timeout=3600, prefix="user_profile")
    def get_user_profile(user_id: int) -> User:
        """
        Retrieve a user's complete profile with related data.

        Uses select_related and prefetch_related to optimize related queries.
        Raises:
            ServiceError: If the user does not exist.
        """
        try:
            user = (
                User.objects.select_related("location")
                .prefetch_related(
                    "favorite_categories",
                    Prefetch(
                        "shops",
                        queryset=Shop.objects.filter(is_verified=True),
                        to_attr="prefetched_shops",
                    ),
                )
                .get(id=user_id)
            )
            return user
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")

    @staticmethod
    @cache_result(timeout=1800, prefix="user_email")
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Retrieve a user by email.
        Returns:
            The user instance if found, else None.
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    @cache_result(timeout=3600, prefix="user_favorites")
    def get_favorite_categories(user_id: int) -> django.db.models.QuerySet[Category]:
        """
        Retrieve a user's favorite categories.
        Returns:
            A QuerySet of Category instances.
        """
        try:
            user = User.objects.get(id=user_id)
            return user.favorite_categories.all()
        except User.DoesNotExist:
            return Category.objects.none()

    @staticmethod
    def _get_user_or_raise(user_id: int) -> User:
        """
        Helper to get a user or raise a ServiceError.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ServiceError(f"User with ID {user_id} not found", code="not_found")

    @staticmethod
    def _get_category_or_raise(category_id: int) -> Category:
        """
        Helper to get a category or raise a ServiceError.
        """
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise ServiceError(
                f"Category with ID {category_id} not found", code="not_found"
            )

    @staticmethod
    def toggle_favorite_category(
        user_id: int, category_id: int
    ) -> Dict[str, Union[bool, str]]:
        """
        Toggle the favorite status of a category for a given user.
        Returns:
            A dictionary indicating success and whether the category was added or removed.
        """
        user = UserService._get_user_or_raise(user_id)
        category = UserService._get_category_or_raise(category_id)

        if category in user.favorite_categories.all():
            user.favorite_categories.remove(category)
            action = "removed"
        else:
            user.favorite_categories.add(category)
            action = "added"

        # Invalidate related caches
        cache.delete(f"user_favorites:{user_id}")
        cache.delete(f"user_profile:{user_id}")

        return {"success": True, "action": action}

    @staticmethod
    def get_personalized_deals(
        user_id: int, limit: int = 10
    ) -> django.db.models.QuerySet[Any]:
        """
        Get personalized deals for a user based on their favorite categories.
        If the user has favorite categories, deals in those categories are returned;
        otherwise, featured deals are returned.
        """
        user = UserService._get_user_or_raise(user_id)
        favorite_categories = user.favorite_categories.all()

        if favorite_categories.exists():
            category_ids = list(favorite_categories.values_list("id", flat=True))
            return DealService.get_deals_by_multiple_categories(category_ids, limit)

        return DealService.get_featured_deals(limit)

    @staticmethod
    def update_notification_preferences(
        user_id: int, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a user's notification preferences.
        Returns:
            The updated notification preferences.
        """
        user = UserService._get_user_or_raise(user_id)
        current_prefs = user.notification_preferences or {}
        current_prefs.update(preferences)

        user.notification_preferences = current_prefs
        user.save(update_fields=["notification_preferences"])

        cache.delete(f"user_profile:{user_id}")
        return user.notification_preferences

    @staticmethod
    def generate_password_reset_token(
        email: str,
    ) -> Optional[Dict[str, Union[int, str]]]:
        """
        Generate a password reset token for a user with the provided email.
        For security, returns None if the email does not exist.
        """
        try:
            user = User.objects.get(email=email)
            token = get_random_string(length=32)
            # Note: This token should be stored securely (e.g., cache, dedicated model)
            # with an expiry and linked to the user for verification later.
            # Returning it directly like this is insecure if not handled properly by the caller.
            return {"user_id": user.id, "token": token}
        except User.DoesNotExist:
            return None
