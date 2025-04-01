"""
Tests for the scrapers app and its integration with other apps.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.contrib.gis.geos import Point

from apps.scrapers.services import ScraperService, CrawlbaseAPIService, DealImportService
from apps.scrapers.models import ScraperJob
from apps.deals.models import Deal
from apps.shops.models import Shop
from apps.locations.models import Location
from tests.fixtures import user, location, category, shop, api_client, authenticated_client, deal


@pytest.mark.django_db
class TestScraperService:
    def test_search_external_sources(self):
        """Test searching external sources with the ScraperService"""
        results = ScraperService.search_external_sources("eco friendly")
        
        # Should return at least one result
        assert len(results) > 0
        assert "title" in results[0]
        assert "description" in results[0]
        assert "original_price" in results[0]
        assert "discounted_price" in results[0]
        assert "discount_percentage" in results[0]
    
    def test_search_external_sources_with_location(self):
        """Test searching external sources with location"""
        results = ScraperService.search_external_sources(
            "eco friendly", latitude=40.7128, longitude=-74.0060
        )
        
        # Should return location-specific results
        assert len(results) > 0
        assert "distance" in results[-1]
    
    @patch("apps.scrapers.services.sync_playwright")
    def test_scrape_shop_deals(self, mock_playwright, shop):
        """Test scraping deals from a shop's website"""
        # Mock Playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        # Mock browser launch
        mock_instance = MagicMock()
        mock_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_instance
        
        # Mock page.evaluate to return deal data
        mock_page.evaluate.return_value = [
            {
                "title": "Test Deal",
                "originalPrice": 100,
                "discountedPrice": 75,
                "discountPercentage": 25,
                "description": "Test description",
                "imageUrl": "https://example.com/image.jpg",
                "productUrl": "https://example.com/product"
            }
        ]
        
        # Set shop website
        shop.website = "https://example.com"
        shop.save()
        
        # Test scrape_shop_deals
        result = ScraperService.scrape_shop_deals(shop.id)
        
        # Check results
        assert result["success"] is True
        assert result["deals_created"] == 1
        assert result["deals_updated"] == 0
        
        # Verify deal was created
        deal = Deal.objects.filter(shop=shop, title="Test Deal").first()
        assert deal is not None
        assert deal.original_price == 100
        assert deal.discounted_price == 75
        assert deal.discount_percentage == 25


@pytest.mark.django_db
class TestCrawlbaseAPIService:
    @patch("apps.scrapers.services.CrawlbaseAPIService.fetch_url")
    @patch("apps.scrapers.services.CrawlbaseAPIService.parse_deals_from_html")
    def test_scrape_and_import_deals(self, mock_parse, mock_fetch, shop):
        """Test scraping and importing deals using Crawlbase API"""
        # Mock responses
        mock_fetch.return_value = {"body": "<html><body></body></html>"}
        mock_parse.return_value = [
            {
                "title": "API Deal",
                "original_price": 200,
                "discounted_price": 150,
                "discount_percentage": 25,
                "description": "API description",
                "image_url": "https://example.com/api-image.jpg",
                "product_url": "https://example.com/api-product",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "city": "New York",
                "country": "USA"
            }
        ]
        
        # Test scrape_and_import_deals
        result = CrawlbaseAPIService.scrape_and_import_deals(
            shop.id, "https://example.com/deals", use_js=True
        )
        
        # Check results
        assert result["success"] is True
        assert result["deals_created"] == 1
        assert result["deals_updated"] == 0
        
        # Verify deal was created
        deal = Deal.objects.filter(shop=shop, title="API Deal").first()
        assert deal is not None
        assert deal.original_price == 200
        assert deal.discounted_price == 150
        assert deal.discount_percentage == 25
        
        # Verify location was created
        location = Location.objects.filter(city="New York", country="USA").first()
        assert location is not None
        assert location.coordinates is not None


@pytest.mark.django_db
class TestDealImportService:
    @patch("apps.scrapers.services.DealImportService.import_from_source")
    def test_import_from_source(self, mock_import, shop):
        """Test importing deals from external sources"""
        # Mock response
        mock_import.return_value = {
            "success": True,
            "created": 5,
            "updated": 2,
            "source": "test_source"
        }
        
        # Test import_from_source
        result = DealImportService.import_from_source("test_source")
        
        # Check results
        assert result["success"] is True
        assert result["created"] == 5
        assert result["updated"] == 2
        assert result["source"] == "test_source"


@pytest.mark.django_db
class TestSearchAPI:
    def test_search_endpoint(self, api_client, deal, shop, category):
        """Test the search API endpoint"""
        # Add category to deal
        deal.categories.add(category)
        
        # Test searching for deals
        response = api_client.get("/api/v1/search/", {"query": "test"})
        
        # Check response
        assert response.status_code == 200
        assert "local_results" in response.data
        assert "external_results" in response.data
        
        # Verify local results
        assert "deals" in response.data["local_results"]
        assert "shops" in response.data["local_results"]
        assert "categories" in response.data["local_results"]
        
        # Verify external results
        assert isinstance(response.data["external_results"], list)
    
    def test_location_search(self, api_client, deal, shop):
        """Test searching by location"""
        # Add coordinates to shop's location
        shop.location.coordinates = Point(0, 0)
        shop.location.save()
        
        # Test searching by location
        response = api_client.get("/api/v1/search/", {
            "latitude": "0",
            "longitude": "0",
            "radius": "10"
        })
        
        # Check response
        assert response.status_code == 200
        assert "local_results" in response.data
        assert "deals" in response.data["local_results"]
        assert "shops" in response.data["local_results"]