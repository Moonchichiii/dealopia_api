"""
Integration tests to verify the interactions between different components of the Dealopia API.

Focuses on testing the key integrations between:
- Accounts & Categories (user favorites)
- Deals & Locations (geo-spatial searches)
- Shops & Products (relationships)
- Search & Scrapers (external data integration)
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services import UserService
from apps.categories.models import Category
from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.locations.models import Location
from apps.products.models import Product
from apps.shops.models import Shop
from apps.shops.services import ShopService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def location_nyc():
    return Location.objects.create(
        city="New York",
        country="United States",
        coordinates=Point(-74.0060, 40.7128),  # longitude, latitude
    )


@pytest.fixture
def location_sf():
    return Location.objects.create(
        city="San Francisco",
        country="United States",
        coordinates=Point(-122.4194, 37.7749),  # longitude, latitude
    )


@pytest.fixture
def eco_category():
    return Category.objects.create(
        name="Eco-Friendly",
        description="Sustainable and eco-friendly products",
        is_active=True,
        is_eco_friendly=True,
    )


@pytest.fixture
def food_category():
    return Category.objects.create(
        name="Food & Drink", description="Food and beverage products", is_active=True
    )


@pytest.fixture
def shop_nyc(user, location_nyc):
    return Shop.objects.create(
        name="NYC Eco Shop",
        owner=user,
        description="Eco-friendly shop in New York",
        short_description="NYC Eco Shop",
        email="nyc@example.com",
        location=location_nyc,
        is_verified=True,
    )


@pytest.fixture
def shop_sf(user, location_sf):
    return Shop.objects.create(
        name="SF Eco Shop",
        owner=user,
        description="Eco-friendly shop in San Francisco",
        short_description="SF Eco Shop",
        email="sf@example.com",
        location=location_sf,
        is_verified=True,
    )


@pytest.fixture
def deal_nyc(shop_nyc, eco_category):
    deal = Deal.objects.create(
        title="NYC Eco Deal",
        shop=shop_nyc,
        description="Sustainable product from NYC",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        is_verified=True,
        sustainability_score=8.5,
    )
    deal.categories.add(eco_category)
    return deal


@pytest.fixture
def deal_sf(shop_sf, eco_category, food_category):
    deal = Deal.objects.create(
        title="SF Organic Food Deal",
        shop=shop_sf,
        description="Organic food from San Francisco",
        original_price=Decimal("50.00"),
        discounted_price=Decimal("40.00"),
        discount_percentage=20,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        is_verified=True,
        sustainability_score=9.0,
    )
    deal.categories.add(eco_category)
    deal.categories.add(food_category)
    return deal


@pytest.fixture
def product(shop_nyc, eco_category):
    product = Product.objects.create(
        name="Eco Product",
        shop=shop_nyc,
        description="A sustainable product",
        price=Decimal("29.99"),
        stock_quantity=100,
    )
    product.categories.add(eco_category)
    return product


@pytest.mark.django_db
class TestUserCategoryIntegration:
    """Test integration between user accounts and categories."""

    def test_toggle_favorite_category(self, user, eco_category):
        """Test toggling a category as favorite for a user."""
        # Initially, user has no favorite categories
        assert user.favorite_categories.count() == 0

        # Add category to favorites
        result = UserService.toggle_favorite_category(user.id, eco_category.id)
        assert result["action"] == "added"

        # Verify category was added to favorites
        user.refresh_from_db()
        assert user.favorite_categories.count() == 1
        assert user.favorite_categories.first() == eco_category

        # Remove category from favorites
        result = UserService.toggle_favorite_category(user.id, eco_category.id)
        assert result["action"] == "removed"

        # Verify category was removed from favorites
        user.refresh_from_db()
        assert user.favorite_categories.count() == 0

    def test_personalized_deals(self, user, eco_category, deal_nyc, deal_sf):
        """Test getting personalized deals based on favorite categories."""
        # Add eco_category to user's favorites
        user.favorite_categories.add(eco_category)

        # Get personalized deals
        deals = UserService.get_personalized_deals(user.id)

        # Should include both deals since they both have the eco_category
        assert len(deals) == 2
        deal_ids = [d.id for d in deals]
        assert deal_nyc.id in deal_ids
        assert deal_sf.id in deal_ids


@pytest.mark.django_db
class TestDealsLocationIntegration:
    """Test integration between deals and locations (geo-spatial features)."""

    def test_get_deals_near_location(self, deal_nyc, deal_sf):
        """Test finding deals near a specific location."""
        # Search near NYC
        nyc_deals = DealService.get_deals_near_location(
            latitude=40.7128, longitude=-74.0060, radius_km=10
        )

        # Should include NYC deal but not SF deal
        assert len(nyc_deals) == 1
        assert nyc_deals[0].id == deal_nyc.id

        # Search near SF
        sf_deals = DealService.get_deals_near_location(
            latitude=37.7749, longitude=-122.4194, radius_km=10
        )

        # Should include SF deal but not NYC deal
        assert len(sf_deals) == 1
        assert sf_deals[0].id == deal_sf.id

    def test_deals_nearby_endpoint(self, api_client, deal_nyc, deal_sf):
        """Test the API endpoint for deals near a location."""
        url = reverse("deals-nearby")
        response = api_client.get(
            url, {"latitude": 40.7128, "longitude": -74.0060, "radius": 10}
        )

        assert response.status_code == status.HTTP_200_OK

        # Check that only NYC deal is included
        assert len(response.data) == 1
        assert response.data[0]["id"] == deal_nyc.id


@pytest.mark.django_db
class TestShopProductIntegration:
    """Test integration between shops and products."""

    def test_shop_products_relationship(self, shop_nyc, product):
        """Test retrieving products for a shop."""
        # Get products for the shop
        shop_products = Product.objects.filter(shop=shop_nyc)

        assert shop_products.count() == 1
        assert shop_products.first().id == product.id

        # Get shop for the product
        assert product.shop.id == shop_nyc.id

    def test_product_deal_relationship(self, shop_nyc, product, deal_nyc, eco_category):
        """Test relationship between products and deals through shops and categories."""
        # Both product and deal belong to the same shop and category
        assert product.shop == deal_nyc.shop
        assert eco_category in product.categories.all()
        assert eco_category in deal_nyc.categories.all()

        # Get active deals for the product
        deals = product.get_active_deals()

        assert deals.count() == 1
        assert deals.first().id == deal_nyc.id


@pytest.mark.django_db
class TestSearchIntegration:
    """Test the search functionality which integrates multiple components."""

    def test_search_by_text(
        self, api_client, deal_nyc, deal_sf, shop_nyc, shop_sf, eco_category
    ):
        """Test searching by text query."""
        url = reverse("search")
        response = api_client.get(url, {"query": "eco"})

        assert response.status_code == status.HTTP_200_OK

        # Check that both deals, shops, and the category are included
        assert len(response.data["local_results"]["deals"]) == 2
        assert len(response.data["local_results"]["shops"]) == 2
        assert len(response.data["local_results"]["categories"]) == 1

    def test_search_by_location(self, api_client, deal_nyc, deal_sf):
        """Test searching by location."""
        url = reverse("search")
        response = api_client.get(
            url, {"latitude": 40.7128, "longitude": -74.0060, "radius": 10}
        )

        assert response.status_code == status.HTTP_200_OK

        # Check that only NYC deal is included
        assert len(response.data["local_results"]["deals"]) == 1
        assert response.data["local_results"]["deals"][0]["title"] == "NYC Eco Deal"

    def test_search_with_external_sources(self, api_client, deal_nyc):
        """Test search with external sources included."""
        url = reverse("search")
        response = api_client.get(url, {"query": "organic", "include_external": "true"})

        assert response.status_code == status.HTTP_200_OK

        # Check that external results are included
        assert "external_results" in response.data
        assert isinstance(response.data["external_results"], list)


@pytest.mark.django_db
class TestCombinedFeatures:
    """Test more complex combinations of features."""

    def test_sustainable_shops_in_location(self, shop_nyc, shop_sf, eco_category):
        """Test finding sustainable shops in a specific location."""
        # Add eco category to both shops
        shop_nyc.categories.add(eco_category)
        shop_sf.categories.add(eco_category)

        # Get shops near NYC that have the eco category
        shops = Shop.objects.filter(
            categories=eco_category,
            location__coordinates__distance_lte=(
                Point(-74.0060, 40.7128),  # NYC coordinates
                10000,  # 10 km in meters
            ),
        ).distinct()

        assert shops.count() == 1
        assert shops.first().id == shop_nyc.id

    def test_user_favorite_deals_in_location(
        self, user, eco_category, deal_nyc, deal_sf
    ):
        """Test finding deals in user's favorite categories near their location."""
        # Add eco category to user's favorites
        user.favorite_categories.add(eco_category)

        # Set user's location to NYC
        user.location = Location.objects.get(city="New York")
        user.save()

        # Get deals in user's favorite categories near their location
        deals = Deal.objects.filter(
            categories__in=user.favorite_categories.all(),
            shop__location__coordinates__distance_lte=(
                user.location.coordinates,
                10000,  # 10 km in meters
            ),
        ).distinct()

        assert deals.count() == 1
        assert deals.first().id == deal_nyc.id
