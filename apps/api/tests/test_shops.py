import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.locations.models import Location
from apps.shops.models import Shop
from apps.shops.services import ShopService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="testuser@example.com", password="StrongPass123!"
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def location():
    return Location.objects.create(
        address="123 Test St",
        city="Test City",
        country="Test Country",
        coordinates=Point(0, 0),
    )


@pytest.fixture
def category():
    return Category.objects.create(
        name="Test Category", description="Test category description"
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
        opening_hours=json.dumps(
            {
                "monday": "9:00-17:00",
                "tuesday": "9:00-17:00",
                "wednesday": "9:00-17:00",
                "thursday": "9:00-17:00",
                "friday": "9:00-17:00",
                "saturday": "Closed",
                "sunday": "Closed",
            }
        ),
        is_verified=True,
    )
    shop.categories.add(category)
    return shop


@pytest.fixture
def deal(shop):
    return Deal.objects.create(
        title="Test Deal",
        shop=shop,
        description="Test deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        is_verified=True,
    )


@pytest.mark.django_db
class TestShopModel:
    def test_shop_creation(self, shop):
        assert shop.id is not None
        assert shop.name == "Test Shop"
        assert shop.owner.email == "testuser@example.com"
        assert shop.is_verified is True
        assert shop.rating == 4.5

    def test_active_deals_count_property(self, shop, deal):
        # Initial count with one active deal
        assert shop.active_deals_count == 1

        # Add another active deal
        Deal.objects.create(
            title="Another Deal",
            shop=shop,
            description="Another deal description",
            original_price=Decimal("50.00"),
            discounted_price=Decimal("25.00"),
            discount_percentage=50,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_verified=True,
        )

        # Count should increase
        assert shop.active_deals_count == 2

        # Add expired deal (shouldn't count)
        Deal.objects.create(
            title="Expired Deal",
            shop=shop,
            description="Expired deal description",
            original_price=Decimal("50.00"),
            discounted_price=Decimal("25.00"),
            discount_percentage=50,
            start_date=timezone.now() - timezone.timedelta(days=10),
            end_date=timezone.now() - timezone.timedelta(days=1),
            is_verified=True,
        )

        # Count should still be 2
        assert shop.active_deals_count == 2

    def test_has_category(self, shop, category):
        assert shop.has_category(category.id) is True

        # Test with non-existent category
        assert shop.has_category(999) is False

        # Test with a different category
        other_category = Category.objects.create(name="Other Category")
        assert shop.has_category(other_category.id) is False

    def test_update_rating(self, shop):
        # Initial rating
        assert shop.rating == 4.5

        # Update rating
        shop.rating = 3.5
        shop.save()

        # Call update_rating
        new_rating = shop.update_rating()

        # Since we don't have reviews in this test, it should return 0
        # In a real scenario, it would calculate the average of reviews
        assert new_rating == 0


@pytest.mark.django_db
class TestShopService:
    def test_get_verified_shops(self, shop):
        verified_shops = ShopService.get_verified_shops()
        assert shop in verified_shops

        # Create an unverified shop
        unverified_shop = Shop.objects.create(
            name="Unverified Shop",
            owner=User.objects.create_user(
                email="unverified@example.com", password="pass"
            ),
            description="Unverified shop description",
            short_description="Unverified shop",
            email="unverified@shop.com",
            location=Location.objects.create(city="City", country="Country"),
            is_verified=False,
        )

        verified_shops = ShopService.get_verified_shops()
        assert shop in verified_shops
        assert unverified_shop not in verified_shops

    def test_get_featured_shops(self, shop):
        # Make shop featured
        shop.is_featured = True
        shop.save()

        featured_shops = ShopService.get_featured_shops()
        assert shop in featured_shops

        # Create a non-featured shop
        non_featured_shop = Shop.objects.create(
            name="Non-featured Shop",
            owner=User.objects.create_user(
                email="non_featured@example.com", password="pass"
            ),
            description="Non-featured shop description",
            short_description="Non-featured shop",
            email="non_featured@shop.com",
            location=Location.objects.create(city="City", country="Country"),
            is_verified=True,
            is_featured=False,
        )

        featured_shops = ShopService.get_featured_shops()
        assert shop in featured_shops
        assert non_featured_shop not in featured_shops

    def test_search_shops(self, shop):
        # Search by name
        results = ShopService.search_shops("Test Shop")
        assert shop in results

        # Search by description
        results = ShopService.search_shops("shop description")
        assert shop in results

        # Search by non-matching term
        results = ShopService.search_shops("Nonexistent")
        assert shop not in results

        # Search with category filter
        category_id = shop.categories.first().id
        results = ShopService.search_shops("", category_id=category_id)
        assert shop in results

    def test_get_shop_with_deals(self, shop, deal):
        result = ShopService.get_shop_with_deals(shop.id)

        assert result["shop"].id == shop.id
        assert len(result["deals"]) == 1
        assert result["deals"][0].id == deal.id


@pytest.mark.django_db
class TestShopAPI:
    def test_list_shops(self, api_client, shop):
        url = reverse("shop-list")
        response = api_client.get(url, format="json")
        assert response.status_code == status.HTTP_200_OK

        # If your API uses pagination, the results may be under the "results" key.
        shops = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        assert len(shops) > 0

        # Find our shop in the returned list
        shop_data = next((item for item in shops if item["id"] == shop.id), None)
        assert shop_data is not None
        assert shop_data["name"] == shop.name

    def test_retrieve_shop(self, api_client, shop):
        url = reverse("shop-detail", args=[shop.id])
        response = api_client.get(url, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == shop.name
        assert response.data["description"] == shop.description
        assert response.data["rating"] == "4.50"

        # Verify location is included
        location_details = response.data.get("location_details")
        assert location_details is not None
        assert location_details["city"] == "Test City"

    def test_create_shop(self, authenticated_client, location, category):
        url = reverse("shop-list")
        print(f"Testing create shop at URL: {url}")
        data = {
            "name": "New Shop",
            "description": "New shop description",
            "short_description": "New shop",
            "email": "new@shop.com",
            "location": location.id,
            "categories": [category.id],
            "opening_hours": json.dumps(
                {
                    "monday": "10:00-18:00",
                    "tuesday": "10:00-18:00",
                    "wednesday": "10:00-18:00",
                    "thursday": "10:00-18:00",
                    "friday": "10:00-18:00",
                    "saturday": "10:00-16:00",
                    "sunday": "Closed",
                }
            ),
        }
        print(f"Sending data: {data}")
        print(f"Location ID: {location.id}, Category ID: {category.id}")

        response = authenticated_client.post(url, data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Shop"

        # Verify in database
        shop = Shop.objects.get(id=response.data["id"])
        print(f"Retrieved shop from DB: {shop.name} (ID: {shop.id})")
        print(f"Shop owner: {shop.owner.email}")
        print(
            f"Shop categories: {list(shop.categories.values_list('name', flat=True))}"
        )

        assert shop.name == "New Shop"
        assert shop.owner.email == "testuser@example.com"
        assert category in shop.categories.all()

    def test_shop_deals_endpoint(self, api_client, shop, deal):
        url = reverse("shop-deals", args=[shop.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id
        assert response.data[0]["title"] == deal.title

    def test_featured_shops_endpoint(self, api_client, shop):
        # Make shop featured
        shop.is_featured = True
        shop.save()

        url = reverse("shop-featured")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == shop.id
