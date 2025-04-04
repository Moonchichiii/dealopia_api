"""
Add a ScraperService class to the apps/scrapers/services.py file.

This implementation allows us to:
1. Keep the existing CrawlbaseAPIService
2. Add the ScraperService that uses CrawlbaseAPIService under the hood
3. Make it compatible with our SearchView
"""

import logging
from typing import Dict, List, Optional
import requests
from django.conf import settings

logger = logging.getLogger("dealopia.scrapers")


class CrawlbaseAPIService:
    """Service for fetching and processing data using the Crawlbase API."""
   
    BASE_URL = "https://api.crawlbase.com"
    NORMAL_TOKEN = getattr(settings, 'CRAWLBASE_NORMAL_TOKEN', None)
    JS_TOKEN = getattr(settings, 'CRAWLBASE_JS_TOKEN', None)

    @classmethod
    def get_api_key(cls, use_js: bool = False) -> str:
        token = cls.JS_TOKEN if use_js else cls.NORMAL_TOKEN
        if not token:
            raise Exception("Crawlbase token not configured.")
        return token

    @classmethod
    def make_request(cls, endpoint: str, method="GET", params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Crawlbase API.
        """
        if not cls.BASE_URL:
            raise Exception("Crawlbase BASE_URL not defined.")

        url = f"{cls.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        default_headers = {
            "Authorization": f"Bearer {cls.get_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.request(method, url, params=params, json=data, headers=default_headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Crawlbase API request error for URL {url}: {e}")
            raise

    @classmethod
    def search_deals(cls, query: str, latitude: Optional[float] = None, longitude: Optional[float] = None, radius_km: float = 10) -> List[Dict]:
        """
        Search for deals using the Crawlbase API.
        This method builds a real API request using your Crawlbase credentials.
        """
        params = {"q": query, "radius": radius_km}
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude

        # Replace '/search' with the actual endpoint provided by your Crawlbase API documentation.
        endpoint = "/search"
        response = cls.make_request(endpoint, method="GET", params=params)
        # Expecting the API to return results under the "results" key.
        if response and "results" in response:
            return response["results"]
        else:
            logger.warning("Crawlbase API did not return any results.")
            return []


class ScraperService:
    """
    Service for scraping and processing external data sources.
    This class serves as a facade for various scraping implementations.
    """
    
    @classmethod
    def search_external_sources(cls, query: Optional[str] = None, latitude: Optional[float] = None, 
                               longitude: Optional[float] = None, radius_km: float = 10) -> List[Dict]:
        """
        Search external sources for deals based on query and/or location.
        
        Args:
            query: Optional search term
            latitude: Optional latitude for location-based search
            longitude: Optional longitude for location-based search
            radius_km: Search radius in kilometers
            
        Returns:
            List of deal dictionaries from external sources
        """
        results = []
        
        # Skip external search if no query and no location
        if not query and (latitude is None or longitude is None):
            return results
            
        try:
            # Use the CrawlbaseAPIService to search for deals
            if query:
                crawlbase_results = CrawlbaseAPIService.search_deals(
                    query=query, 
                    latitude=latitude, 
                    longitude=longitude, 
                    radius_km=radius_km
                )
                results.extend(crawlbase_results)
            
            # If we only have location (no query), do a location-only search
            elif latitude is not None and longitude is not None:
                crawlbase_results = CrawlbaseAPIService.search_deals(
                    query="", 
                    latitude=latitude, 
                    longitude=longitude, 
                    radius_km=radius_km
                )
                results.extend(crawlbase_results)
                
        except Exception as e:
            logger.error(f"Error searching external sources: {e}")
            
        return results
    
    @classmethod
    def process_external_results(cls, results: List[Dict]) -> List[Dict]:
        """
        Process and normalize results from external sources.
        
        Args:
            results: Raw results from external sources
            
        Returns:
            Processed and normalized results
        """
        processed_results = []
        
        for result in results:
            # Normalize the result format
            processed_result = {
                "title": result.get("title", ""),
                "description": result.get("description", ""),
                "original_price": result.get("original_price", 0),
                "discounted_price": result.get("discounted_price", 0),
                "shop_name": result.get("shop_name", ""),
                "source": result.get("source", "external"),
                "url": result.get("url", ""),
                "distance": result.get("distance", None),
            }
            
            # Calculate discount percentage if not provided
            if "discount_percentage" not in result and processed_result["original_price"] > 0:
                original = float(processed_result["original_price"])
                discounted = float(processed_result["discounted_price"])
                if original > 0:
                    discount = ((original - discounted) / original) * 100
                    processed_result["discount_percentage"] = round(discount, 2)
            else:
                processed_result["discount_percentage"] = result.get("discount_percentage", 0)
                
            processed_results.append(processed_result)
            
        return processed_results