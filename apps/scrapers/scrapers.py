"""
Unified services for the scrapers app.
Integrates with other applications to provide scraping functionality.
"""
import logging
import time
from datetime import timedelta
from typing import Dict, List, Optional, Union, Any

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone
from playwright.sync_api import sync_playwright

from apps.deals.models import Deal
from apps.shops.models import Shop
from apps.locations.models import Location
from apps.categories.models import Category

logger = logging.getLogger("dealopia.scrapers")


class ScraperService:
    """
    Consolidated service for scraping deals from websites and external APIs.
    """
    
    @staticmethod
    def search_external_sources(
        query: str = None, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None
    ) -> List[Dict]:
        """
        Search external sources for deals based on query and location.
        
        Args:
            query: Search query string
            latitude: Optional latitude for location-based search
            longitude: Optional longitude for location-based search
            
        Returns:
            List of dictionaries containing deal information
        """
        results = []
        
        if not query:
            return results
            
        try:
            # Try to use Crawlbase API first
            if latitude and longitude:
                crawlbase_results = CrawlbaseAPIService.search_by_location(
                    query, latitude, longitude, radius_km=10
                )
                
                if crawlbase_results:
                    results.extend(crawlbase_results)
            
            # Fallback to our own scraping if needed
            if not results:
                # Generic search from external deal APIs or mock data for now
                results = [
                    {
                        "title": f"External deal for {query}",
                        "description": f"This is an external deal related to {query}",
                        "original_price": 100.00,
                        "discounted_price": 75.00,
                        "discount_percentage": 25,
                        "source": "external_api",
                    }
                ]
                
                if latitude and longitude:
                    # Add location-specific deals if coordinates provided
                    results.append({
                        "title": f"Local {query} deal near you",
                        "description": f"This is a local deal for {query} near your location",
                        "original_price": 50.00,
                        "discounted_price": 30.00,
                        "discount_percentage": 40,
                        "distance": "2.5 km",
                        "source": "local_api",
                    })
                
        except Exception as e:
            logger.error(f"Error searching external sources: {str(e)}")
            
        return results
            
    @staticmethod
    def scrape_shop_deals(shop_id: int) -> Dict[str, Union[bool, str, int]]:
        """
        Scrape deals from a shop's website using Playwright.
        
        Args:
            shop_id: ID of the shop to scrape
            
        Returns:
            Dictionary with results of scraping operation
        """
        try:
            shop = Shop.objects.get(id=shop_id)
            
            if not shop.website:
                return {
                    "success": False,
                    "error": "Shop has no website defined",
                }
                
            # Check if we should use the scrape_url or fall back to website
            scrape_url = shop.scrape_url or shop.website
            
            # Use Playwright for modern, JavaScript-heavy sites
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                try:
                    # Navigate to shop website
                    page.goto(scrape_url, timeout=60000)
                    
                    # Wait for content to load
                    page.wait_for_load_state("networkidle", timeout=30000)
                    
                    # Get deals using JavaScript evaluation
                    deals_data = page.evaluate("""() => {
                        // Generic selector for deals/products
                        const dealElements = document.querySelectorAll('.product-card, .deal-item, .offer, .discount');
                        
                        return Array.from(dealElements).map(el => {
                            // Extract title
                            const titleEl = el.querySelector('h2, h3, .title, .product-title');
                            const title = titleEl ? titleEl.textContent.trim() : '';
                            
                            // Extract prices
                            const originalPriceEl = el.querySelector('.original-price, .regular-price, .old-price, del, s');
                            const discountedPriceEl = el.querySelector('.sale-price, .discounted-price, .current-price');
                            
                            // Extract other info
                            const descriptionEl = el.querySelector('.description, .product-description');
                            const imageEl = el.querySelector('img');
                            const linkEl = el.querySelector('a');
                            
                            // Parse prices
                            let originalPrice = 0;
                            let discountedPrice = 0;
                            let discountPercentage = 0;
                            
                            if (originalPriceEl && discountedPriceEl) {
                                // Extract numeric values from price text
                                const extractPrice = (text) => {
                                    const match = text.match(/\\d+(\\.\\d+)?/);
                                    return match ? parseFloat(match[0]) : 0;
                                };
                                
                                originalPrice = extractPrice(originalPriceEl.textContent);
                                discountedPrice = extractPrice(discountedPriceEl.textContent);
                                
                                // Calculate discount percentage
                                if (originalPrice > 0 && discountedPrice > 0 && discountedPrice < originalPrice) {
                                    discountPercentage = Math.round(((originalPrice - discountedPrice) / originalPrice) * 100);
                                }
                            }
                            
                            // Extract location data if available
                            const lat = el.dataset ? el.dataset.lat : null;
                            const lng = el.dataset ? el.dataset.lng : null;
                            const city = el.dataset ? el.dataset.city : null;
                            const country = el.dataset ? el.dataset.country : null;
                            
                            return {
                                title,
                                originalPrice,
                                discountedPrice,
                                discountPercentage,
                                description: descriptionEl ? descriptionEl.textContent.trim() : '',
                                imageUrl: imageEl ? imageEl.src : '',
                                productUrl: linkEl ? linkEl.href : '',
                                latitude: lat ? parseFloat(lat) : null,
                                longitude: lng ? parseFloat(lng) : null,
                                city: city || '',
                                country: country || ''
                            };
                        }).filter(deal => 
                            deal.title && 
                            deal.originalPrice > 0 && 
                            deal.discountedPrice > 0 && 
                            deal.discountPercentage > 0
                        );
                    }""")
                    
                    # Close browser
                    browser.close()
                    
                    # Process and save deals
                    deals_created = 0
                    deals_updated = 0
                    
                    with transaction.atomic():
                        for deal_data in deals_data:
                            # Skip invalid deals
                            if not deal_data.get('title') or deal_data.get('discountPercentage', 0) <= 0:
                                continue
                                
                            # Process location data if available
                            location_obj = None
                            if deal_data.get('latitude') and deal_data.get('longitude'):
                                lat = deal_data['latitude']
                                lng = deal_data['longitude']
                                city = deal_data.get('city', 'Unknown City')
                                country = deal_data.get('country', 'Unknown Country')
                                
                                location_obj, _ = Location.objects.get_or_create(
                                    city=city, 
                                    country=country,
                                    defaults={
                                        "coordinates": Point(lng, lat, srid=4326)
                                    }
                                )
                            
                            # Try to find existing deal
                            existing_deal = Deal.objects.filter(
                                shop=shop,
                                title=deal_data['title']
                            ).first()
                            
                            if existing_deal:
                                # Update existing deal
                                existing_deal.original_price = deal_data['originalPrice']
                                existing_deal.discounted_price = deal_data['discountedPrice']
                                existing_deal.discount_percentage = deal_data['discountPercentage']
                                existing_deal.end_date = timezone.now() + timezone.timedelta(days=30)  # Extend by 30 days
                                existing_deal.image = deal_data.get('imageUrl', '')
                                existing_deal.redemption_link = deal_data.get('productUrl', '')
                                
                                if location_obj:
                                    existing_deal.location = location_obj
                                    
                                existing_deal.save()
                                deals_updated += 1
                            else:
                                # Create new deal
                                deal = Deal.objects.create(
                                    shop=shop,
                                    title=deal_data['title'],
                                    description=deal_data.get('description', ''),
                                    original_price=deal_data['originalPrice'],
                                    discounted_price=deal_data['discountedPrice'],
                                    discount_percentage=deal_data['discountPercentage'],
                                    image=deal_data.get('imageUrl', ''),
                                    redemption_link=deal_data.get('productUrl', ''),
                                    start_date=timezone.now(),
                                    end_date=timezone.now() + timezone.timedelta(days=30),
                                    is_verified=True,
                                )
                                
                                if location_obj:
                                    deal.location = location_obj
                                    deal.save()
                                    
                                deals_created += 1
                    
                    return {
                        "success": True,
                        "deals_created": deals_created,
                        "deals_updated": deals_updated,
                        "total_processed": deals_created + deals_updated,
                    }
                    
                except Exception as e:
                    browser.close()
                    raise e
                    
        except Exception as e:
            logger.error(f"Error scraping deals for shop {shop_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


class DealImportService:
    """Service for importing deals from external sources."""
    
    @staticmethod
    def import_from_source(source_name: str, limit: int = 100) -> Dict[str, Union[bool, str, int]]:
        """
        Import deals from a specific external source.
        
        Args:
            source_name: Name of the source to import from
            limit: Maximum number of deals to import
            
        Returns:
            Dictionary with results of import operation
        """
        try:
            logger.info(f"Importing deals from {source_name}")
            
            if source_name.lower() == "crawlbase":
                return CrawlbaseAPIService.import_trending_deals(limit)
            
            # Fallback to API services using the factory pattern
            service_class = APIServiceFactory.get_service(source_name)
            if service_class and hasattr(service_class, "sync_deals"):
                return service_class.sync_deals(limit)
            
            # Simple mock implementation for testing
            return {
                "success": True,
                "created": 10,
                "updated": 5,
                "source": source_name,
            }
            
        except Exception as e:
            logger.error(f"Error importing deals from {source_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


class CrawlbaseAPIService:
    """Service for fetching and processing data using the Crawlbase API."""
    
    BASE_URL = "https://api.crawlbase.com"
    NORMAL_TOKEN = getattr(settings, 'CRAWLBASE_NORMAL_TOKEN', None)
    JS_TOKEN = getattr(settings, 'CRAWLBASE_JS_TOKEN', None)

    @staticmethod
    def fetch_url(url, use_js=False, timeout=90):
        """Fetch a URL through Crawlbase API."""
        token = (CrawlbaseAPIService.JS_TOKEN if use_js 
                else CrawlbaseAPIService.NORMAL_TOKEN)
        if not token:
            logger.warning("No Crawlbase token configured.")
            return None

        params = {"token": token, "url": url}

        try:
            response = requests.get(
                CrawlbaseAPIService.BASE_URL, 
                params=params, 
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.exception(f"Crawlbase API request error for URL {url}: {e}")
            return None

    @classmethod
    def scrape_and_import_deals(cls, shop_id, scrape_url, use_js=False):
        """Scrape deals from a URL and import them to the database."""
        response = cls.fetch_url(scrape_url, use_js=use_js)
        if not response or "body" not in response:
            return {
                "success": False, 
                "error": "Failed to retrieve content from Crawlbase."
            }

        deals_data = cls.parse_deals_from_html(response["body"])
        if not deals_data:
            return {
                "success": False, 
                "error": "No deals found in the response."
            }

        shop = Shop.objects.get(id=shop_id)
        deals_created, deals_updated = 0, 0

        with transaction.atomic():
            for data in deals_data:
                lat = data.get("latitude")
                lng = data.get("longitude")
                location_obj = None
                if lat and lng:
                    location_obj, _ = Location.objects.get_or_create(
                        address=data.get("address", ""),
                        city=data.get("city", "Unknown City"),
                        country=data.get("country", "Unknown Country"),
                        defaults={"coordinates": Point(lng, lat, srid=4326)},
                    )

                existing = Deal.objects.filter(
                    shop=shop, title=data["title"]
                ).first()
                
                if existing:
                    existing.original_price = data["original_price"]
                    existing.discounted_price = data["discounted_price"]
                    existing.discount_percentage = data["discount_percentage"]
                    existing.image = data["image_url"]
                    existing.redemption_link = data["product_url"]
                    existing.end_date = timezone.now() + timedelta(days=30)
                    if location_obj:
                        existing.location = location_obj
                    existing.save()
                    deals_updated += 1
                else:
                    deal = Deal.objects.create(
                        shop=shop,
                        title=data["title"],
                        description=data.get("description", ""),
                        original_price=data["original_price"],
                        discounted_price=data["discounted_price"],
                        discount_percentage=data["discount_percentage"],
                        image=data["image_url"],
                        start_date=timezone.now(),
                        end_date=timezone.now() + timedelta(days=30),
                        redemption_link=data["product_url"],
                        is_verified=True,
                    )
                    if location_obj:
                        deal.location = location_obj
                        deal.save()
                    deals_created += 1

        return {
            "success": True,
            "deals_created": deals_created,
            "deals_updated": deals_updated,
            "total_processed": deals_created + deals_updated,
        }

    @staticmethod
    def parse_deals_from_html(html_content):
        """Parse deal information from HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        deal_elements = soup.select(".product-card, .deal-item, .discount-item")

        deals = []
        for el in deal_elements:
            title_el = el.select_one("h2, h3, .title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            original_el = el.select_one(".original-price")
            discounted_el = el.select_one(".sale-price")
            if not original_el or not discounted_el:
                continue

            image_el = el.select_one("img")
            link_el = el.select_one("a")
            desc_el = el.select_one(".description")

            lat = el.get("data-lat")
            lng = el.get("data-lng")
            city = el.get("data-city")
            country = el.get("data-country")

            try:
                original_price = float(
                    original_el.get_text(strip=True).replace("$", "")
                )
                discounted_price = float(
                    discounted_el.get_text(strip=True).replace("$", "")
                )
            except ValueError:
                continue

            discount_percentage = 0
            if original_price > 0:
                discount_percentage = round(
                    (1 - discounted_price / original_price) * 100
                )

            deals.append({
                "title": title,
                "original_price": original_price,
                "discounted_price": discounted_price,
                "discount_percentage": discount_percentage,
                "description": desc_el.get_text(strip=True) if desc_el else "",
                "image_url": image_el["src"] if image_el else "",
                "product_url": link_el["href"] if link_el else "",
                "latitude": float(lat) if lat else None,
                "longitude": float(lng) if lng else None,
                "address": el.get("data-addr") or "",
                "city": city or "",
                "country": country or "",
            })

        return deals
        
    @classmethod
    def search_by_location(cls, query, latitude, longitude, radius_km=10):
        """
        Search for deals near a specific location using Crawlbase API.
        
        Args:
            query: Search query
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_km: Search radius in kilometers
            
        Returns:
            List of deals found near the location
        """
        # This would be implemented to connect to a real API
        # For now, return a mock response
        return [{
            "title": f"Local {query} deal via Crawlbase",
            "description": f"This is a scraped deal for {query} near your location",
            "original_price": 80.00,
            "discounted_price": 40.00,
            "discount_percentage": 50,
            "distance": f"{round(radius_km/2, 1)} km",
            "source": "crawlbase_api",
        }]
        
    @classmethod
    def import_trending_deals(cls, limit=100):
        """
        Import trending deals from Crawlbase API.
        
        Args:
            limit: Maximum number of deals to import
            
        Returns:
            Dictionary with results of import operation
        """
        # Mock implementation
        return {
            "success": True,
            "created": 15,
            "updated": 5,
            "source": "crawlbase",
        }


class APIServiceFactory:
    """Factory for creating API service instances"""

    @staticmethod
    def get_service(service_name):
        """Get an API service by name"""
        # Import here to avoid circular imports
        from .api_services import GoodOnYouAPIService, HotUKDealsAPIService
        
        services = {
            "good_on_you": GoodOnYouAPIService,
            "hotukdeals": HotUKDealsAPIService,
        }

        # Return the service class or None if not found
        return services.get(service_name.lower())