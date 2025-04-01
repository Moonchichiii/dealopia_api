from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.services import UserService
from apps.categories.models import Category

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def authenticated_client(api_client, user_data):
    user = User.objects.create_user(**user_data)
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self, user_data):
        user = User.objects.create_user(**user_data)
        assert user.email == user_data["email"]
        assert user.first_name == user_data["first_name"]
        assert user.check_password(user_data["password"])
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com", password="AdminPass123!"
        )
        assert superuser.is_staff
        assert superuser.is_superuser
        assert superuser.email == "admin@example.com"

    def test_get_full_name(self, user_data):
        user = User.objects.create_user(**user_data)
        assert (
            user.get_full_name()
            == f"{user_data['first_name']} {user_data['last_name']}"
        )

    def test_email_change_request(self, user_data):
        user = User.objects.create_user(**user_data)
        new_email = "new_email@example.com"

        # Create email change request
        token = user.create_email_change_request(new_email)

        # Verify token was created
        assert user.email_change_token is not None
        assert user.new_email == new_email
        assert user.email_token_created_at is not None

        # Test confirm email change
        user.confirm_email_change(token)
        assert user.email == new_email
        assert user.new_email is None
        assert user.email_change_token is None

    def test_email_change_with_expired_token(self, user_data):
        user = User.objects.create_user(**user_data)
        new_email = "new_email@example.com"

        # Create email change request with expired token
        token = user.create_email_change_request(new_email)

        # Set token creation time to more than a day ago
        user.email_token_created_at = timezone.now() - timedelta(days=2)
        user.save()

        # Confirm should fail with expired token
        with pytest.raises(ValueError):
            user.confirm_email_change(token)

        # Email should not be changed
        assert user.email == user_data["email"]


@pytest.mark.django_db
class TestUserService:
    def test_get_user_profile(self, user_data):
        user = User.objects.create_user(**user_data)
        retrieved_user = UserService.get_user_profile(user.id)
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email

    def test_get_user_by_email(self, user_data):
        user = User.objects.create_user(**user_data)
        retrieved_user = UserService.get_user_by_email(user.email)
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email

    def test_toggle_favorite_category(self, user_data):
        user = User.objects.create_user(**user_data)
        category = Category.objects.create(name="Test Category", description="Test")

        # Test adding to favorites
        result = UserService.toggle_favorite_category(user.id, category.id)
        assert result["action"] == "added"

        user.refresh_from_db()
        assert category in user.favorite_categories.all()

        # Test removing from favorites
        result = UserService.toggle_favorite_category(user.id, category.id)
        assert result["action"] == "removed"

        user.refresh_from_db()
        assert category not in user.favorite_categories.all()

    def test_update_notification_preferences(self, user_data):
        user = User.objects.create_user(**user_data)
        preferences = {
            "email_notifications": False,
            "deals_notifications": True,
        }

        result = UserService.update_notification_preferences(user.id, preferences)
        assert result["email_notifications"] == False
        assert result["deals_notifications"] == True

        user.refresh_from_db()
        assert user.notification_preferences["email_notifications"] == False
        assert user.notification_preferences["deals_notifications"] == True


@pytest.mark.django_db
class TestUserAPI:
    def test_me_endpoint(self, authenticated_client):
        client, user = authenticated_client
        url = reverse("user-me")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name

    def test_profile_update(self, authenticated_client):
        client, user = authenticated_client
        url = reverse("user-profile")
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "preferred_language": "fr",
        }

        response = client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
        assert response.data["last_name"] == "Name"
        assert response.data["preferred_language"] == "fr"

        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.preferred_language == "fr"

    def test_password_change(self, authenticated_client, user_data):
        client, user = authenticated_client
        url = reverse("user-change-password")
        data = {
    "current_password": user_data["password"],
    "new_password": "NewPassword123!",
    "new_password_confirm": "NewPassword123!",
}


        response = client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data

        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password("NewPassword123!")
