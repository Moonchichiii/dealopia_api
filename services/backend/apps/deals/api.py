import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger("dealopia.api")


class EcoRetailerAPI:
    """Integration service for open sustainable retailer APIs."""

    SOURCES = {
        "open_food_facts": {
            "url": "https://world.openfoodfacts.org",
            "key_setting": None,
            "is_sustainable": True,
        },
        "open_apparel_registry": {
            "url": "https://api.openapparel.org",
            "key_setting": None,
            "is_sustainable": True,
        },
    }

    def __init__(self, source: str):
        """
        Initialize API client for the specified sustainable retail source.

        Args:
            source: Name of the retail source to connect to

        Raises:
            ValueError: If source is not supported
        """
        if source not in self.SOURCES:
            raise ValueError(f"Unsupported API source: {source}")

        self.source = source
        self.config = self.SOURCES[source]
        self.base_url = self.config["url"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Dealopia/1.0 (sustainable-shopping-app)",
            }
        )

    def fetch_deal_by_barcode(self, barcode: str):
        """
        Fetch product information by barcode from Open Food Facts.

        Args:
            barcode: Product barcode to look up

        Returns:
            List of standardized deal dictionaries

        Raises:
            ValueError: If called on non-supported source
        """
        if self.source != "open_food_facts":
            raise ValueError("Barcode fetch is only supported for Open Food Facts")

        url = f"{self.base_url}/api/v0/product/{barcode}.json"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return self._parse_open_food_facts(response.json())
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return []

    def fetch_facilities(self, **params):
        """
        Fetch facility information from Open Apparel Registry.

        Args:
            **params: Query parameters for the API request

        Returns:
            List of standardized facility dictionaries

        Raises:
            ValueError: If called on non-supported source
        """
        if self.source != "open_apparel_registry":
            raise ValueError(
                "Facility fetch is only supported for Open Apparel Registry"
            )

        url = f"{self.base_url}/facilities"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return self._parse_open_apparel_registry(response.json())
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return []

    def _parse_open_food_facts(self, data):
        """
        Parse Open Food Facts API response into standardized format.

        Args:
            data: Raw API response data

        Returns:
            List of standardized deal dictionaries
        """
        product = data.get("product", {})
        if not product:
            return []

        eco_score = product.get("ecoscore_score", 5.0)
        standardized_deal = {
            "title": product.get("product_name", "Unknown product"),
            "description": product.get("generic_name", ""),
            "original_price": Decimal("0"),
            "discounted_price": Decimal("0"),
            "discount_percentage": 0,
            "image_url": product.get("image_url"),
            "redemption_link": product.get("url"),
            "shop_name": product.get("brands", "Open Food Facts"),
            "shop_website": product.get("brands_tags", [""])[0],
            "eco_certifications": product.get("labels_tags", []),
            "source": "open_food_facts",
            "external_id": f"off-{product.get('id')}",
            "sustainability_score": float(eco_score),
            "category_names": product.get("categories_tags", []),
        }
        return [standardized_deal]

    def _parse_open_apparel_registry(self, data):
        """
        Parse Open Apparel Registry API response into standardized format.

        Args:
            data: Raw API response data

        Returns:
            List of standardized facility dictionaries
        """
        facilities = data.get("features", [])
        standardized_facilities = []
        for facility in facilities:
            props = facility.get("properties", {})
            standardized_facilities.append(
                {
                    "name": props.get("name"),
                    "address": props.get("address"),
                    "country": props.get("country_name"),
                    "contributors": props.get("contributors", []),
                    "eco_certifications": props.get("certificates", []),
                    "source": "open_apparel_registry",
                    "external_id": props.get("id"),
                    "sustainability_score": 7.0,  # Static score
                }
            )
        return standardized_facilities
