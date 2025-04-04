import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from decimal import Decimal
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model

from apps.deals.models import Deal
from apps.shops.models import Shop
from apps.categories.models import Category
from apps.locations.models import Location

User = get_user_model()

@pytest.mark.django_db
class TestSearchView:
    @pytest.fixture
    def client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        
    @pytest.fixture
    def location(self):
        return Location.objects.create(
            city="Test City",
            country="Test Country",
            coordinates=Point(12.34, 56.78, srid=4326)
        )

    @pytest.fixture
    def shop(self, location, user):
        return Shop.objects.create(
            name="Test Shop",
            short_description="A test shop",
            website="https://testshop.example.com",
            is_verified=True,
            location=location,
            owner=user
        )

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name="Test Category",
            description="A test category",
            is_active=True,
        )

    @pytest.fixture
    def deal(self, shop, category):
        deal = Deal.objects.create(
            shop=shop,
            title="Test Deal",
            description="A test deal",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("80.00"),
            discount_percentage=20,
            sustainability_score=8.0,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_verified=True,
        )
        deal.categories.add(category)
        return deal

    def test_search_with_query(self, client, deal, shop, category):
        """
        Test the search endpoint with a query parameter.
        """
        url = reverse("search")
        response = client.get(url, {"query": "Test"})
        assert response.status_code == 200
        data = response.data

        assert "local_results" in data
        local = data["local_results"]
        assert "deals" in local
        assert "shops" in local
        assert "categories" in local

    def test_search_with_location(self, client, shop, deal):
        """
        Test searching by location.
        """
        url = reverse("search")
        response = client.get(url, {
            "latitude": "56.78",
            "longitude": "12.34",
            "radius": "10"
        })
        assert response.status_code == 200
        data = response.data

        local = data["local_results"]
        assert "deals" in local
        assert "shops" in local

    def test_search_external_results(self, client, deal, shop, category):
        """
        Test that external search results are returned as a list.
        """
        url = reverse("search")
        response = client.get(url, {"query": "Test", "include_external": "true"})
        assert response.status_code == 200
        data = response.data

        assert "external_results" in data
        assert isinstance(data["external_results"], list)
