import logging
from typing import Dict, List, Optional
from django.conf import settings
import requests

logger = logging.getLogger("dealopia.scrapers")


class CrawlbaseAPIService:
    """
    Service for fetching and processing data using the Crawlbase API.
    """
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
    def make_request(cls, endpoint: str, method="GET", params=None, data=None, headers=None) -> Dict:
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
        if headers:
            default_headers.update(headers)
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
        Search for deals using the real Crawlbase API.
        This method calls the external search endpoint (for example, using https://data.europa.eu/api/hub/search/)
        with the given query and location parameters.
        """
        params = {"q": query, "radius": radius_km}
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude

        # Assuming the real search endpoint is at '/search'
        endpoint = "/search"
        response = cls.make_request(endpoint, method="GET", params=params)
        # Process the response based on the actual API structure.
        return response.get("results", [])


class ScraperService:
    """
    Consolidated service for scraping deals from external APIs.
    """

    @staticmethod
    def search_external_sources(query: str, latitude: Optional[float] = None, longitude: Optional[float] = None, radius: float = 10) -> List[Dict]:
        """
        Search external sources for deals using the Crawlbase API.
        """
        try:
            results = CrawlbaseAPIService.search_deals(query, latitude, longitude, radius_km=radius)
            return results
        except Exception as e:
            logger.error(f"Error during external search: {str(e)}")
            return []
