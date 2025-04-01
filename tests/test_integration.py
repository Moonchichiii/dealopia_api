from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.services import UserService
from apps.categories.models import Category
from apps.categories.services import CategoryService
from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.locations.models import Location
from apps.locations.services import LocationService
from apps.shops.models import Shop
from apps.shops.services import ShopService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="testuser@example.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def location():
    return Location.objects.create(
        address="123 Main St",
        city="Test City",
        state="Test State",
        country="Test Country",
        postal_code="12345",
        coordinates=Point(0, 0),
    )


@pytest.fixture
def category():
    return Category.objects.create(
        name="Test Category", description="Test category description", is_active=True
    )


@pytest.fixture
def shop(user, location, category):
    shop = Shop.objects.create(
        name="Test Shop",
        owner=user,
        description="Test shop description",
        short_description="Test shop",
        email="shop@example.com",
        location=location,
        rating=4.5,
        is_verified=True,
    )
    shop.categories.add(category)
    return shop


@pytest.fixture
def deal(shop, category):
    deal = Deal.objects.create(
        title="Test Deal",
        shop=shop,
        description="Test deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        sustainability_score=8.5,
        is_verified=True,
    )
    deal.categories.add(category)
    return deal


@pytest.mark.django_db
class TestUserShopIntegration:
    """Tests for the integration between User and Shop models/services"""

    def test_user_shops_relationship(self, user, shop):
        # User should be owner of the shop
        assert shop in user.shops.all()
        assert shop.owner == user

    def test_shop_creation_by_authenticated_user(
        self, authenticated_client, location, category
    ):
        url = reverse("shop-list")
        data = {
            "name": "New User Shop",
            "description": "Shop created by user",
            "short_description": "User shop",
            "email": "usershop@example.com",
            "location": location.id,
            "categories": [category.id],
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify shop was created and linked to the user
        user = User.objects.get(email="testuser@example.com")
        shop = Shop.objects.get(id=response.data["id"])

        assert shop.owner == user
        assert shop in user.shops.all()


@pytest.mark.django_db
class TestShopDealIntegration:
    """Tests for the integration between Shop and Deal models/services"""

    def test_shop_deals_relationship(self, shop, deal):
        # Deal should be associated with the shop
        assert deal in shop.deals.all()
        assert deal.shop == shop

        # Active deal count should be 1
        assert shop.active_deals_count == 1

    def test_deal_creation_for_shop(self, authenticated_client, shop, category):
        url = reverse("deal-list")
        data = {
            "title": "New Shop Deal",
            "shop": shop.id,
            "description": "New deal for shop",
            "original_price": "120.00",
            "discounted_price": "90.00",
            "discount_percentage": 25,
            "start_date": (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "categories": [category.id],
            "is_verified": True,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify deal was created and linked to the shop
        shop.refresh_from_db()
        deal = Deal.objects.get(id=response.data["id"])

        assert deal.shop == shop
        assert deal in shop.deals.all()
        assert shop.active_deals_count == 2

    def test_shop_deals_endpoint(self, api_client, shop, deal):
        url = reverse("shop-deals", args=[shop.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == deal.id
        assert response.data[0]["title"] == deal.title


@pytest.mark.django_db
class TestShopLocationIntegration:
    """Tests for the integration between Shop and Location models/services"""

    def test_shop_location_relationship(self, shop, location):
        # Shop should have a location
        assert shop.location == location

    def test_create_shop_with_location(self, authenticated_client, location, category):
        url = reverse("shop-list")
        data = {
            "name": "Location-based Shop",
            "description": "Shop with location",
            "short_description": "Location shop",
            "email": "locationshop@example.com",
            "location": location.id,
            "categories": [category.id],
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify shop was created with the correct location
        shop = Shop.objects.get(id=response.data["id"])
        assert shop.location == location

    def test_nearby_shops_by_location(self, api_client, shop, location):
        # Add latitude and longitude to query, searching near the shop's location
        url = reverse("location-nearby")
        params = {
            "lat": location.latitude,
            "lng": location.longitude,
            "radius": 10,
            "include_deals": "true",
        }

        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "locations" in response.data
        assert "deals" in response.data

        # The location should be in the results
        location_ids = [item["id"] for item in response.data["locations"]]
        assert location.id in location_ids


@pytest.mark.django_db
class TestDealCategoryIntegration:
    """Tests for the integration between Deal and Category models/services"""

    def test_deal_category_relationship(self, deal, category):
        # Deal should be in the category
        assert category in deal.categories.all()
        assert deal in category.deals.all()

    def test_create_deal_with_category(self, authenticated_client, shop, category):
        url = reverse("deal-list")
        data = {
            "title": "Category Deal",
            "shop": shop.id,
            "description": "Deal with category",
            "original_price": "150.00",
            "discounted_price": "100.00",
            "discount_percentage": 33,
            "start_date": (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "categories": [category.id],
            "is_verified": True,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify deal was created with the correct category
        deal = Deal.objects.get(id=response.data["id"])
        assert category in deal.categories.all()

    def test_category_deals_endpoint(self, api_client, deal, category):
        url = reverse("category-deals", args=[category.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id
        assert response.data[0]["title"] == deal.title


@pytest.mark.django_db
class TestUserCategoryIntegration:
    """Tests for the integration between User and Category models/services"""

    def test_user_favorite_categories(self, user, category):
        # Add category to user's favorites
        user.favorite_categories.add(category)

        # Verify the relationship
        assert category in user.favorite_categories.all()

    def test_toggle_favorite_category(self, user, category):
        # Initially, category should not be in favorites
        assert category not in user.favorite_categories.all()

        # Toggle (add) category to favorites
        result = UserService.toggle_favorite_category(user.id, category.id)
        assert result["action"] == "added"

        user.refresh_from_db()
        assert category in user.favorite_categories.all()

        # Toggle (remove) category from favorites
        result = UserService.toggle_favorite_category(user.id, category.id)
        assert result["action"] == "removed"

        user.refresh_from_db()
        assert category not in user.favorite_categories.all()

    def test_personalized_deals(self, user, deal, category):
        # Add category to user's favorites
        user.favorite_categories.add(category)

        # Get personalized deals
        personalized_deals = UserService.get_personalized_deals(user.id)

        # Since deal is in the favorited category, it should be in the result
        assert deal in personalized_deals


@pytest.mark.django_db
class TestSustainabilityIntegration:
    """Tests for integration related to sustainability features across applications"""

    def test_sustainable_deals_filtering(self, api_client, deal):
        # Set sustainability score
        deal.sustainability_score = 9.0
        deal.save()

        # Query the sustainable deals endpoint
        url = reverse("deal-sustainable")
        params = {"min_score": 8.5}
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id

        # Increase min_score threshold to exclude the deal
        params = {"min_score": 9.5}
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_eco_certifications(self, authenticated_client, deal):
        # Set eco certifications
        deal.eco_certifications = ["Organic", "Fair Trade"]
        deal.local_production = True
        deal.save()

        # Calculate sustainability score
        before_score = deal.sustainability_score
        deal.calculate_sustainability_score()
        after_score = deal.sustainability_score

        # Score should increase with eco certifications and local production
        assert after_score > before_score

        # Retrieve deal to verify
        url = reverse("deal-detail", args=[deal.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["eco_certifications"] == ["Organic", "Fair Trade"]
        assert response.data["local_production"] is True


@pytest.mark.django_db
class TestComplexDataFlowIntegration:
    """Tests for more complex data flows that cross multiple applications"""

    def test_full_user_shop_deal_flow(
        self, authenticated_client, user, location, category
    ):
        # Step 1: User creates a shop
        shop_url = reverse("shop-list")
        shop_data = {
            "name": "User Flow Shop",
            "description": "Test shop for full flow",
            "short_description": "Flow shop",
            "email": "flow@example.com",
            "location": location.id,
            "categories": [category.id],
        }

        shop_response = authenticated_client.post(shop_url, shop_data)
        assert shop_response.status_code == status.HTTP_201_CREATED
        shop_id = shop_response.data["id"]

        # Step 2: User creates a deal for the shop
        deal_url = reverse("deal-list")
        deal_data = {
            "title": "Flow Deal",
            "shop": shop_id,
            "description": "Deal for flow testing",
            "original_price": "200.00",
            "discounted_price": "150.00",
            "discount_percentage": 25,
            "start_date": (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            "categories": [category.id],
            "is_verified": True,
            "sustainability_score": 8.0,
        }

        deal_response = authenticated_client.post(deal_url, deal_data)
        assert deal_response.status_code == status.HTTP_201_CREATED
        deal_id = deal_response.data["id"]

        # Step 3: User adds category to favorites
        # Using the service directly as there might not be an API endpoint for this
        result = UserService.toggle_favorite_category(user.id, category.id)
        assert result["action"] == "added"

        # Step 4: Verify personalized deals include the created deal
        personalized_deals = UserService.get_personalized_deals(user.id)
        created_deal = Deal.objects.get(id=deal_id)
        assert created_deal in personalized_deals

        # Step 5: Track deal interaction
        track_url = reverse("deal-track-view", args=[deal_id])
        track_response = authenticated_client.post(track_url)
        assert track_response.status_code == status.HTTP_200_OK

        # Step 6: Check shop deals endpoint includes the new deal
        shop_deals_url = reverse("shop-deals", args=[shop_id])
        shop_deals_response = authenticated_client.get(shop_deals_url)
        assert shop_deals_response.status_code == status.HTTP_200_OK
        assert len(shop_deals_response.data) > 0
        assert shop_deals_response.data[0]["id"] == deal_id

        # Step 7: Check nearby deals includes the new deal
        nearby_url = reverse("location-nearby")
        params = {
            "lat": location.latitude,
            "lng": location.longitude,
            "radius": 10,
            "include_deals": "true",
        }

        nearby_response = authenticated_client.get(nearby_url, params)
        assert nearby_response.status_code == status.HTTP_200_OK

        # The deal should be in the results
        deal_ids = [item["id"] for item in nearby_response.data["deals"]]
        assert deal_id in deal_ids

    def test_sustainability_score_affects_related_entities(self, deal, shop, category):
        # Verify that sustainability features propagate across the system

        # Set high sustainability score
        deal.sustainability_score = 9.5
        deal.eco_certifications = ["Organic", "Fair Trade", "Carbon Neutral"]
        deal.local_production = True
        deal.save()

        # Get sustainable deals
        sustainable_deals = DealService.get_sustainable_deals(min_score=9.0)
        assert deal in sustainable_deals

        # Get popular categories (should include category since it has a sustainable deal)
        popular_categories = CategoryService.get_popular_categories()
        assert category in popular_categories

        # Clean up non-relevant data
        Deal.objects.exclude(id=deal.id).delete()

        # Get featured shops (shop should be there since it has a featured sustainable deal)
        # First mark the deal as featured
        deal.is_featured = True
        deal.save()

        # Mark shop as verified
        shop.is_verified = True
        shop.save()

        # Get featured shops
        shop.refresh_from_db()
        featured_shops = ShopService.get_featured_shops()
        assert shop in featured_shops


@pytest.mark.django_db
class TestAPIEndpointIntegrations:
    """Tests for API endpoints that involve multiple applications"""

    def test_location_with_deals_endpoint(self, api_client, location, shop, deal):
        # Test endpoint that fetches locations with nearby deals
        url = reverse("location-nearby")
        params = {
            "lat": location.latitude,
            "lng": location.longitude,
            "radius": 10,
            "include_deals": "true",
        }

        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "locations" in response.data
        assert "deals" in response.data

        # Verify location and deal are included
        location_ids = [item["id"] for item in response.data["locations"]]
        deal_ids = [item["id"] for item in response.data["deals"]]

        assert location.id in location_ids
        assert deal.id in deal_ids

    def test_shop_active_deals_count(self, api_client, shop, deal):
        # Test that shop API includes correct active deals count
        url = reverse("shop-detail", args=[shop.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "deal_count" in response.data
        assert response.data["deal_count"] == 1

        # Add another active deal
        Deal.objects.create(
            title="Another Deal",
            shop=shop,
            description="Another deal description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_verified=True,
        )

        # Check count increased
        response = api_client.get(url)
        assert response.data["deal_count"] == 2

    def test_category_parent_child_relationships(self, api_client):
        # Create parent category
        parent = Category.objects.create(
            name="Parent Category", description="Parent category", is_active=True
        )

        # Create child category
        child = Category.objects.create(
            name="Child Category",
            description="Child category",
            parent=parent,
            is_active=True,
        )

        # Test parent category endpoint includes child
        url = reverse("category-detail", args=[parent.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "children" in response.data

        children_ids = [item["id"] for item in response.data["children"]]
        assert child.id in children_ids

        # Test child category shows parent
        url = reverse("category-detail", args=[child.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "parent" in response.data
        assert response.data["parent"] == parent.id

    def test_deal_with_shop_and_categories(self, api_client, deal, shop, category):
        # Test that deal API includes shop and category data
        url = reverse("deal-detail", args=[deal.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify shop data is included
        assert "shop" in response.data
        assert response.data["shop"]["id"] == shop.id
        assert response.data["shop"]["name"] == shop.name

        # Verify category data is included
        assert "categories" in response.data
        category_ids = [item["id"] for item in response.data["categories"]]
        assert category.id in category_ids


@pytest.mark.django_db
class TestEdgeCaseIntegrations:
    """Tests for edge cases and error handling in integrations"""

    def test_user_without_favorite_categories(self, user):
        # User with no favorite categories should still get deals
        deals = UserService.get_personalized_deals(user.id)

        # Should return featured deals instead
        assert isinstance(deals, list)

    def test_deal_without_categories(self, shop):
        # Create deal without categories
        deal = Deal.objects.create(
            title="Uncategorized Deal",
            shop=shop,
            description="Deal with no categories",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("80.00"),
            discount_percentage=20,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_verified=True,
        )

        # Get related deals
        related_deals = DealService.get_related_deals(deal)

        # Should handle case where deal has no categories
        assert isinstance(related_deals, list)

    def test_location_without_coordinates(self):
        # Create location without coordinates
        location = Location.objects.create(
            address="No Coordinates", city="Test City", country="Test Country"
        )

        # Verify latitude and longitude properties handle None
        assert location.latitude is None
        assert location.longitude is None

    def test_expired_deal_not_in_active_deals(self, shop, category):
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

        # Expired deal should not be returned in category deals endpoint
        url = reverse("category-deals", args=[category.id])
        response = APIClient().get(url)

        assert response.status_code == status.HTTP_200_OK
        deal_ids = [item["id"] for item in response.data]
        assert expired_deal.id not in deal_ids
