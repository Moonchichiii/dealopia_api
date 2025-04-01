from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.scrapers.services import DealImportService
from apps.categories.models import Category
from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.deals.tasks import (
    clean_expired_deals,
    import_deals_from_apis,
    scrape_sustainable_deals,
    send_deal_notifications,
    update_sustainability_scores,
)
from apps.locations.models import Location
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(email="testuser@example.com", password="StrongPass123!")


@pytest.fixture
def location():
    return Location.objects.create(city="Test City", country="Test Country", coordinates=Point(0, 0))


@pytest.fixture
def shop(user, location):
    return Shop.objects.create(
        name="Test Shop",
        owner=user,
        description="Test shop description",
        short_description="Test shop",
        email="shop@example.com",
        location=location,
        rating=4.5,
    )


@pytest.fixture
def category():
    return Category.objects.create(name="Test Category", description="Test category description")


@pytest.fixture
def deal(shop, category):
    deal = Deal.objects.create(
        title="Test Deal",
        shop=shop,
        description="Test deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timedelta(days=1),
        end_date=timezone.now() + timedelta(days=7),
        sustainability_score=8.0,  # Updated
        is_verified=True,
    )
    deal.categories.add(category)
    return deal


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestDealAPI:
    def test_list_deals(self, api_client, deal):
        url = reverse("deal-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["results"], list)  # Updated
        assert len(response.data["results"]) > 0  # Added
        assert response.data["results"][0]["title"] == deal.title  # Updated

    def test_retrieve_deal(self, api_client, deal):
        url = reverse("deal-detail", args=[deal.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == deal.title
        assert response.data["shop"]["name"] == deal.shop.name
        assert Decimal(response.data["original_price"]) == deal.original_price

    def test_create_deal(self, authenticated_client, shop, category):
        url = reverse("deal-list")
        data = {
            "title": "New Deal",
            "shop": shop.id,
            "description": "New deal description",
            "original_price": "120.00",
            "discounted_price": "90.00",
            "discount_percentage": 25,
            "start_date": (timezone.now() - timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timedelta(days=7)).isoformat(),
            "categories": [category.id],
            "is_verified": True,
            "image": "https://example.com/test-image.jpg",  # Added
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_featured_deals_endpoint(self, api_client, deal):
        deal.is_featured = True
        deal.save()

        url = reverse("deal-featured")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == deal.id

    def test_sustainable_deals_endpoint(self, api_client, deal):
        url = reverse("deal-sustainable")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id

        # Test with higher min_score parameter
        url = f"{url}?min_score=9.0"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0  # Deal has score of 8.0


@pytest.mark.django_db
class TestDealModel:
    def test_deal_creation(self, deal):
        assert deal.id is not None
        assert deal.title == "Test Deal"
        assert deal.original_price == Decimal("100.00")
        assert deal.discount_percentage == 20
        assert deal.is_active is True

    def test_is_active_property(self, shop):
        active_deal = Deal.objects.create(
            title="Active Deal",
            shop=shop,
            description="Description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_verified=True,
        )
        assert active_deal.is_active is True

        expired_deal = Deal.objects.create(
            title="Expired Deal",
            shop=shop,
            description="Description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=1),
            is_verified=True,
        )
        assert expired_deal.is_active is False

    def test_discount_amount_property(self, deal):
        assert deal.discount_amount == Decimal("20.00")


@pytest.mark.django_db
class TestDealService:
    def test_get_active_deals(self, deal):
        active_deals = DealService.get_active_deals()
        assert deal in active_deals

        deal.end_date = timezone.now() - timedelta(days=1)
        deal.save()

        active_deals = DealService.get_active_deals()
        assert deal not in active_deals

    def test_search_deals(self, deal):
        results = DealService.search_deals("Test Deal")
        assert deal in results

        results = DealService.search_deals("Nonexistent")
        assert deal not in results

    def test_get_sustainable_deals(self, deal):
        sustainable_deals = DealService.get_sustainable_deals(min_score=3.0)
        assert deal in sustainable_deals

        sustainable_deals = DealService.get_sustainable_deals(min_score=9.0)
        assert deal not in sustainable_deals


class TestDealTasks:
    @patch("apps.scrapers.services.DealImportService")  # Updated
    @patch("apps.deals.tasks.EcoRetailerAPI")
    @patch("apps.deals.tasks.logger")
    def test_import_deals_from_apis(self, mock_logger, mock_eco_retailer_api, mock_deal_import_service):
        mock_eco_retailer_api.SOURCES = {"source1": {}, "source2": {}}
        mock_deal_import_service.import_from_source.side_effect = [
            {"success": True, "created": 5, "updated": 3},
            {"success": False, "error": "API error"},
        ]

        result = import_deals_from_apis()

        assert mock_deal_import_service.import_from_source.call_count == 2
        assert result["total_created"] == 5
        assert "source2" in result["failed_sources"]

    @patch("apps.deals.tasks.CrawlerProcess")
    @patch("apps.deals.tasks.get_project_settings")
    @patch("apps.deals.tasks.SustainableDealSpider")
    def test_scrape_sustainable_deals_success(self, mock_spider, mock_get_settings, mock_crawler_process):
        process_instance = MagicMock()
        mock_crawler_process.return_value = process_instance
        mock_get_settings.return_value = {"SETTING": "value"}

        result = scrape_sustainable_deals()

        mock_crawler_process.assert_called_once()
        process_instance.crawl.assert_called_once_with(mock_spider)
        process_instance.start.assert_called_once()
        assert result["success"] is True

    @pytest.mark.django_db
    def test_clean_expired_deals(self, shop):
        active_deal = Deal.objects.create(
            title="Active Deal",
            shop=shop,
            original_price=Decimal("100"),
            discounted_price=Decimal("80"),
            discount_percentage=20,  # Added
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=5),
            is_verified=True,
        )
        expired_deal = Deal.objects.create(
            title="Expired Deal",
            shop=shop,
            original_price=Decimal("100"),
            discounted_price=Decimal("80"),
            discount_percentage=20,  # Added
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            is_verified=True,
        )

        result = clean_expired_deals()
        assert result["deleted"] == 1
        assert Deal.objects.filter(id=active_deal.id).exists()
        assert not Deal.objects.filter(id=expired_deal.id).exists()
