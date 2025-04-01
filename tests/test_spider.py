import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import responses
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.locations.models import Location
from apps.scrapers.api_services import (BaseAPIService, GoodOnYouAPIService,
                                        HotUKDealsAPIService)
from apps.scrapers.services import ScraperService
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        email="admin@example.com", password="AdminPass123!"
    )


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def location():
    return Location.objects.create(
        city="Test City", country="Test Country", coordinates=Point(0, 0)
    )


@pytest.fixture
def shop(admin_user, location):
    shop = Shop.objects.create(
        name="Test Shop",
        owner=admin_user,
        description="Test shop description",
        short_description="Test shop",
        email="shop@example.com",
        location=location,
        website="https://testshop.com",
        is_verified=True,
    )
    return shop


@pytest.fixture
def category():
    return Category.objects.create(
        name="Test Category", description="Test category description", is_active=True
    )


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
        is_verified=True,
        sustainability_score=8.5,
    )
    deal.categories.add(category)
    return deal


@pytest.mark.django_db
class TestExternalAPIIntegration:
    """Tests for integration with external APIs via the scraper services"""

    @responses.activate
    @patch("apps.scrapers.api_services.settings")
    def test_good_on_you_api_integration(
        self, mock_settings, authenticated_client, category
    ):
        # Configure mock settings
        mock_settings.GOOD_ON_YOU_API_KEY = "test_api_key"

        # Mock the brands API endpoint
        api_url = "https://api.goodonyou.eco/api/v1/brands"
        responses.add(
            responses.GET,
            api_url,
            json={"brands": [{"id": 1, "name": "Eco Brand", "rating": 4.5}]},
            status=200,
        )

        # Mock the brand details API endpoint
        brand_url = "https://api.goodonyou.eco/api/v1/brands/1"
        responses.add(
            responses.GET,
            brand_url,
            json={
                "id": 1,
                "name": "Eco Brand",
                "description": "Sustainable fashion brand",
                "rating": 4.5,
                "website": "https://ecobrand.com",
                "featured_products": [
                    {
                        "name": "Eco Shirt",
                        "description": "Organic cotton shirt",
                        "price": 100,
                        "sale_price": 80,
                        "image_url": "https://example.com/image.jpg",
                        "url": "https://ecobrand.com/products/shirt",
                    }
                ],
            },
            status=200,
        )

        # Use the API service to sync brands
        result = GoodOnYouAPIService.sync_sustainable_brands(limit=1)

        # Verify result
        assert result["success"] is True
        assert result["shops_created"] >= 1

        # Verify the shop was created
        shop = Shop.objects.filter(name="Eco Brand").first()
        assert shop is not None
        assert shop.description == "Sustainable fashion brand"
        assert shop.website == "https://ecobrand.com"

        # Verify deals were created
        deals = Deal.objects.filter(shop=shop)
        assert deals.count() > 0
        assert deals.first().title == "Eco Shirt"
        assert deals.first().original_price == Decimal("100")
        assert deals.first().discounted_price == Decimal("80")

    @responses.activate
    @patch("apps.scrapers.api_services.settings")
    def test_hotukdeals_api_integration(
        self, mock_settings, authenticated_client, category
    ):
        # Configure mock settings
        mock_settings.HOTUKDEALS_API_KEY = "test_api_key"

        # Mock the deals API endpoint
        api_url = "https://api.hotukdeals.com/rest/deals/hot"
        responses.add(
            responses.GET,
            api_url,
            json={
                "deals": [
                    {
                        "id": 1,
                        "title": "Eco Deal",
                        "description": "Sustainable product with recycled materials",
                        "merchant": {
                            "name": "Eco Shop",
                            "website": "https://ecoshop.com",
                        },
                        "price": {"original": 100, "current": 75},
                        "category": {"name": "Fashion"},
                        "image": "https://example.com/image.jpg",
                        "url": "https://ecoshop.com/deal1",
                    }
                ]
            },
            status=200,
        )

        # Use the API service to sync deals
        result = HotUKDealsAPIService.sync_uk_deals(limit=1)

        # Verify result
        assert result["success"] is True
        assert result["deals_created"] >= 1

        # Verify the shop was created
        shop = Shop.objects.filter(name="Eco Shop").first()
        assert shop is not None
        assert shop.website == "https://ecoshop.com"

        # Verify deals were created
        deals = Deal.objects.filter(shop=shop)
        assert deals.count() > 0
        assert deals.first().title == "Eco Deal"
        assert deals.first().original_price == Decimal("100")
        assert deals.first().discounted_price == Decimal("75")
        assert "recycled" in deals.first().description.lower()


@pytest.mark.django_db
class TestScraperIntegration:
    """Tests for integration between scraper service and other components"""

    @patch("apps.scrapers.services.sync_playwright")
    def test_scraper_service_integration(
        self, mock_playwright, authenticated_client, shop, category
    ):
        # Mock Playwright
        playwright_instance = MagicMock()
        chromium = MagicMock()
        browser = MagicMock()
        page = MagicMock()

        # Set up chain of mocks
        mock_playwright.return_value.__enter__.return_value = playwright_instance
        playwright_instance.chromium = chromium
        chromium.launch.return_value = browser
        browser.new_page.return_value = page

        # Mock page.evaluate to return deals
        page.evaluate.return_value = [
            {
                "title": "Scraped Eco Deal",
                "originalPrice": 200,
                "discountedPrice": 150,
                "discountPercentage": 25,
                "imageUrl": "https://example.com/image1.jpg",
                "productUrl": "https://testshop.com/deal1",
                "description": "Scraped eco-friendly product",
            }
        ]

        # Use the scraper service to scrape deals
        result = ScraperService.scrape_shop_deals(shop.id)

        # Verify result
        assert result["success"] is True
        assert result["deals_created"] == 1

        # Verify deal was created
        deals = Deal.objects.filter(title="Scraped Eco Deal")
        assert deals.count() == 1

        # Verify deal properties
        deal = deals.first()
        assert deal.shop == shop
        assert deal.original_price == Decimal("200")
        assert deal.discounted_price == Decimal("150")
        assert deal.discount_percentage == 25
        assert deal.redemption_link == "https://testshop.com/deal1"

        # Retrieve the deal via API
        url = reverse("deal-detail", args=[deal.id])
        response = authenticated_client.get(url)

        # Verify API response
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Scraped Eco Deal"
        assert response.data["shop"]["name"] == shop.name
        assert Decimal(response.data["original_price"]) == Decimal("200")
        assert Decimal(response.data["discounted_price"]) == Decimal("150")


@pytest.mark.django_db
class TestAPIEndpoints:
    """Tests for API endpoints that interact with scraped data"""

    @patch("apps.scrapers.services.ScraperService.scrape_shop_deals")
    def test_shop_scrape_endpoint(self, mock_scrape, authenticated_client, shop):
        # Mock scraper result
        mock_scrape.return_value = {
            "success": True,
            "deals_created": 5,
            "deals_updated": 2,
            "total_processed": 7,
        }

        # Create API endpoint (assuming there is one)
        url = reverse("shop-detail", args=[shop.id])
        url = f"{url}scrape/"  # Add scrape action to URL

        response = authenticated_client.post(url)

        # Verify API response
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["deals_created"] == 5

        # Verify scraper was called
        mock_scrape.assert_called_once_with(shop.id)

    @responses.activate
    @patch("apps.scrapers.api_services.settings")
    def test_import_brands_endpoint(self, mock_settings, authenticated_client):
        # Configure mock settings
        mock_settings.GOOD_ON_YOU_API_KEY = "test_api_key"

        # Mock the brands API endpoint
        api_url = "https://api.goodonyou.eco/api/v1/brands"
        responses.add(responses.GET, api_url, json={"brands": []}, status=200)

        # Create API endpoint (assuming there is one)
        url = reverse("admin-import-brands")

        response = authenticated_client.post(
            url, {"source": "good_on_you", "limit": 10}
        )

        # Verify API response
        assert response.status_code == status.HTTP_200_OK
        assert "task_id" in response.data

    @patch("apps.deals.tasks.clean_expired_deals.delay")
    def test_cleanup_deals_endpoint(self, mock_task, authenticated_client):
        # Create API endpoint (assuming there is one)
        url = reverse("admin-cleanup-deals")

        response = authenticated_client.post(url, {"days": 90})

        # Verify API response
        assert response.status_code == status.HTTP_200_OK
        assert "task_id" in response.data

        # Verify task was called
        mock_task.assert_called_once_with(days=90)
