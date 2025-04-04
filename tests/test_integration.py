"""
Fixes for integration tests based on the error patterns:

1. Deal creation failures (HTTP 400 instead of 201)
2. Issues with sustainability score calculations
3. Problems with parent-child relationships in categories
4. Issues with returning lists vs QuerySets
5. Problems with expired deals still showing in active deals
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.deals.models import Deal
from apps.shops.models import Shop
from apps.categories.models import Category
from apps.locations.models import Location
from apps.deals.services import DealService
from apps.shops.services import ShopService
from apps.categories.services import CategoryService
from apps.users.services import UserService

User = get_user_model()

# Fix 1: Deal creation tests
@pytest.mark.django_db
class TestDealCreation:
    def test_create_deal_with_required_fields(self, client, shop, category):
        """Test that deals can be created with required fields."""
        url = reverse("deal-list")
        data = {
            "title": "Test Deal",
            "shop": shop.id,
            "description": "A test deal",
            "original_price": "100.00",
            "discounted_price": "80.00",
            "start_date": timezone.now().isoformat(),
            "end_date": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "categories": [category.id],
        }
        
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

# Fix 2: Sustainability score calculation
@pytest.mark.django_db
class TestSustainabilityScore:
    def test_sustainability_score_calculation(self, deal):
        """Test sustainability score calculation."""
        # Set initial score
        initial_score = 5.0
        deal.sustainability_score = initial_score
        deal.save()
        
        # Add eco certifications and calculate score
        deal.eco_certifications = ["Organic", "Fair Trade"]
        deal.local_production = True
        deal.calculate_sustainability_score()
        
        # Score should increase with eco certifications and local production
        assert deal.sustainability_score > initial_score

# Fix 3: Category parent-child relationships
@pytest.mark.django_db
class TestCategoryRelationships:
    def test_category_serialization_includes_subcategories(self, api_client):
        # Create parent and child categories
        parent = Category.objects.create(
            name="Parent Category", 
            description="Parent category", 
            is_active=True
        )
        
        child = Category.objects.create(
            name="Child Category",
            description="Child category",
            parent=parent,
            is_active=True,
        )
        
        # Test API response
        url = reverse("category-detail", args=[parent.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert "subcategories" in response.data  # Use subcategories instead of children
        assert len(response.data["subcategories"]) == 1
        assert response.data["subcategories"][0]["id"] == child.id

# Fix 4: List vs QuerySet issue
@pytest.mark.django_db
class TestServiceReturns:
    def test_user_service_returns_list(self, user):
        """Test that UserService.get_personalized_deals returns a list."""
        # Mock implementation of get_personalized_deals if needed
        deals = UserService.get_personalized_deals(user.id)
        
        # The method should return a list, even if empty
        assert isinstance(deals, list)
    
    def test_deal_service_returns_list(self, deal):
        """Test that DealService.get_related_deals returns a list."""
        # Make sure get_related_deals returns a list
        related_deals = DealService.get_related_deals(deal)
        
        # The method should return a list, even if empty
        assert isinstance(related_deals, list)

# Fix 5: Expired deals showing in active deals
@pytest.mark.django_db
class TestExpiredDeals:
    def test_expired_deals_excluded(self, shop, category):
        """Test that expired deals are not included in active deals."""
        # Create expired deal
        expired_deal = Deal.objects.create(
            title="Expired Deal",
            shop=shop,
            description="This deal has expired",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("80.00"),
            discount_percentage=20,
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now() - timezone.timedelta(days=1),
            is_verified=True,
        )
        expired_deal.categories.add(category)
        
        # Get active deals
        active_deals = DealService.get_active_deals()
        
        # Expired deal should not be in active deals
        assert expired_deal not in active_deals
        
        # Category deals API should not include expired deals
        url = reverse("category-deals", args=[category.id])
        response = APIClient().get(url)
        
        assert response.status_code == status.HTTP_200_OK
        deal_ids = [item["id"] for item in response.data]
        assert expired_deal.id not in deal_ids