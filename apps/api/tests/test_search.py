"""Tests for the search app and its integrated web scraping functionality."""

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
from apps.search.services import GooglePlacesService
from apps.search.web_scraper.services import WebScraperService
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="AdminPass123!"
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(email="test@example.com", password="password123")


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def location(db):
    return Location.objects.create(
        city="Test City",
        country="Test Country",
        coordinates=Point(12.34, 56.78, srid=4326),
    )


@pytest.fixture
def shop(db, admin_user, location):
    return Shop.objects.create(
        name="Test Shop",
        owner=admin_user,
        description="Test shop description",
        short_description="Test shop",
        email="shop@example.com",
        location=location,
        website="https://testshop.com",
        is_verified=True,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Test Category", description="Test category description", is_active=True
    )


@pytest.fixture
def deal(db, shop, category):
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
class TestSearchView:
    """Test the search endpoint that unifies results."""

    def test_search_with_query(self, api_client, deal, shop, category):
        """Test the search endpoint with a query parameter."""
        url = reverse("search")
        response = api_client.get(url, {"query": "Test"})
        assert response.status_code == 200
        data = response.data

        assert "local_results" in data
        local = data["local_results"]
        assert "deals" in local
        assert "shops" in local
        assert "categories" in local

        # Verify deals are returned correctly
        assert len(local["deals"]) > 0
        assert local["deals"][0]["title"] == "Test Deal"
        assert local["deals"][0]["shop_name"] == "Test Shop"

    def test_search_with_location(self, api_client, shop, deal):
        """Test searching by location."""
        url = reverse("search")
        response = api_client.get(
            url, {"latitude": "56.78", "longitude": "12.34", "radius": "10"}
        )
        assert response.status_code == 200
        data = response.data

        local = data["local_results"]
        assert "deals" in local
        assert "shops" in local

        # Verify location-based results
        if len(local["deals"]) > 0:
            assert "distance" in local["deals"][0]
        if len(local["shops"]) > 0:
            assert "distance" in local["shops"][0]

    def test_search_with_filters(self, api_client, deal, category):
        """Test search with category and sustainability filters."""
        url = reverse("search")
        response = api_client.get(
            url,
            {
                "query": "Test",
                "category": str(category.id),
                "min_sustainability": "7.0",
            },
        )
        assert response.status_code == 200
        data = response.data

        # Verify filtered results
        local_deals = data["local_results"]["deals"]
        if len(local_deals) > 0:
            assert local_deals[0]["sustainability_score"] >= 7.0

    def test_search_external_results(self, api_client, deal, shop, category):
        """Test that external search results are returned as a list."""
        url = reverse("search")
        response = api_client.get(url, {"query": "Test", "include_external": "true"})
        assert response.status_code == 200
        data = response.data

        assert "external_results" in data
        assert isinstance(data["external_results"], list)

    def test_invalid_coordinates(self, api_client):
        """Test validation of coordinate parameters."""
        url = reverse("search")
        response = api_client.get(url, {"latitude": "invalid", "longitude": "12.34"})
        assert response.status_code == 400
        assert "error" in response.data


@pytest.mark.django_db
class TestWebScraperService:
    """Tests for the web scraper service functionality."""

    @patch("apps.search.web_scraper.services.sync_playwright")
    def test_analyze_shop_website(self, mock_playwright, shop):
        """Test analyzing a website for sustainability information."""
        # Set up mocks for Playwright
        playwright_instance = MagicMock()
        browser = MagicMock()
        context = MagicMock()
        page = MagicMock()

        mock_playwright.return_value.__enter__.return_value = playwright_instance
        playwright_instance.chromium.launch.return_value = browser
        browser.new_context.return_value = context
        context.new_page.return_value = page

        # Mock page responses
        page.content.return_value = """
        <html>
            <head><title>Eco Shop</title></head>
            <body>
                <h1>Welcome to our eco-friendly store</h1>
                <p>We sell sustainable products made from recycled materials.</p>
                <a href="/sustainability">Our Sustainability Commitment</a>
                <img src="/eco-badge.png" alt="Certified Green Business">
            </body>
        </html>
        """
        page.title.return_value = "Eco Shop"
        page.evaluate.return_value = "An eco-friendly online store"

        # Test the analyze method
        result = WebScraperService.analyze_shop_website("https://example.com")

        # Verify the result structure
        assert "name" in result
        assert "description" in result
        assert "sustainability" in result
        assert "analyzed_at" in result

        # Verify sustainability score calculation
        sustainability = result["sustainability"]
        assert "score" in sustainability
        assert "keywords_found" in sustainability
        assert "eco_links" in sustainability

        # Check keyword detection
        assert "eco-friendly" in sustainability["keywords_found"]
        assert "sustainable" in sustainability["keywords_found"]
        assert "recycled" in sustainability["keywords_found"]

    @patch("apps.search.web_scraper.services.sync_playwright")
    def test_analyze_deals_page(self, mock_playwright, shop):
        """Test analyzing a shop's deals page for sustainable deals."""
        # Set up mocks for Playwright
        playwright_instance = MagicMock()
        browser = MagicMock()
        page = MagicMock()

        mock_playwright.return_value.__enter__.return_value = playwright_instance
        playwright_instance.chromium.launch.return_value = browser
        browser.new_page.return_value = page

        # Mock page.evaluate to return scraped deals
        page.evaluate.return_value = [
            {
                "title": "Eco-friendly T-shirt",
                "originalPrice": 40,
                "discountedPrice": 30,
                "discountPercentage": 25,
                "description": "Made from organic cotton",
                "imageUrl": "https://example.com/tshirt.jpg",
                "productUrl": "https://example.com/products/tshirt",
                "isSustainable": True,
            },
            {
                "title": "Regular T-shirt",
                "originalPrice": 30,
                "discountedPrice": 20,
                "discountPercentage": 33,
                "description": "Cotton t-shirt",
                "imageUrl": "https://example.com/regular.jpg",
                "productUrl": "https://example.com/products/regular",
                "isSustainable": False,
            },
        ]

        # Test the analyze_deals_page method
        result = WebScraperService.analyze_deals_page(
            shop.id, "https://example.com/deals"
        )

        # Verify the result structure
        assert "success" in result
        assert result["success"] is True
        assert "deals_found" in result
        assert "sustainable_deals" in result
        assert "deal_data" in result

        # Verify sustainability filtering
        assert result["deals_found"] == 2
        assert result["sustainable_deals"] == 1
        assert len(result["deal_data"]) == 1
        assert "Eco-friendly" in result["deal_data"][0]["title"]


@pytest.mark.django_db
class TestGooglePlacesService:
    """Tests for Google Places API integration."""

    @responses.activate
    @patch("apps.search.services.settings")
    def test_search_google_places(self, mock_settings):
        """Test searching for sustainable shops via Google Places API."""
        # Configure mock settings
        mock_settings.GOOGLE_PLACES_API_KEY = "test_api_key"

        # Mock the Google Places API endpoint
        api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        responses.add(
            responses.GET,
            api_url,
            json={
                "results": [
                    {
                        "place_id": "abc123",
                        "name": "Green Store",
                        "vicinity": "123 Eco Street, Test City",
                        "geometry": {"location": {"lat": 56.7, "lng": 12.3}},
                        "icon": "https://maps.gstatic.com/icon.png",
                    }
                ],
                "status": "OK",
            },
            status=200,
        )

        # Test the search method
        results = GooglePlacesService.search(
            query="sustainable store", latitude=56.78, longitude=12.34, radius_km=10
        )

        # Verify the result structure
        assert len(results) > 0
        assert "id" in results[0]
        assert "name" in results[0]
        assert "description" in results[0]
        assert "sustainability_score" in results[0]
        assert "distance" in results[0]
        assert "source" in results[0]

        # Verify content
        assert results[0]["name"] == "Green Store"
        assert results[0]["source"] == "google_places"

    def test_calculate_sustainability_score(self):
        """Test sustainability score calculation."""
        # Create a sample place
        place = {
            "name": "Eco-friendly Store",
            "vicinity": "Sells sustainable, organic products",
        }

        # Test the score calculation
        score = GooglePlacesService._calculate_sustainability_score(place)

        # Verify score calculation based on keywords
        assert score > 5.0  # Base score is 5.0
        assert score <= 10.0  # Should be capped at 10.0


@pytest.mark.django_db
class TestCeleryTasks:
    """Tests for Celery tasks in the search app."""

    @patch("apps.search.web_scraper.services.WebScraperService.analyze_shop_website")
    def test_analyze_website_task(self, mock_analyze, shop):
        """Test the analyze_website Celery task."""
        from apps.search.models import ScraperJob
        from apps.search.web_scraper.tasks import analyze_website

        # Mock the analysis result
        mock_analyze.return_value = {
            "name": "Test Shop",
            "description": "A sustainable shop",
            "sustainability": {
                "score": 8.5,
                "keywords_found": ["eco-friendly", "sustainable"],
                "eco_links": ["/sustainability"],
                "sustainability_images": 1,
            },
        }

        # Run the task
        result = analyze_website(shop.website)

        # Verify task completed successfully
        assert result["success"] is True
        assert "result" in result

        # Verify ScraperJob creation and update
        job = ScraperJob.objects.filter(source_url=shop.website).first()
        assert job is not None
        assert job.status == "completed"
        assert job.completed_at is not None
        assert job.sustainability_score == Decimal("8.5")
