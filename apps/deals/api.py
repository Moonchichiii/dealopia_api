import logging
from decimal import Decimal
from urllib.parse import urlparse

import requests
from cloudinary.uploader import upload
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.shops.models import Shop

logger = logging.getLogger("dealopia.api")


class EcoRetailerAPI:
    """Integration service for eco-friendly retailer APIs."""

    # Supported API sources
    SOURCES = {
        "good_on_you": {
            "url": "https://api.goodonyou.eco/api/v1",
            "key_setting": "GOOD_ON_YOU_API_KEY",
            "is_sustainable": True,
        },
        "hotukdeals": {
            "url": "https://api.hotukdeals.com/rest",
            "key_setting": "HOTUKDEALS_API_KEY",
            "is_sustainable": False,  # Requires additional sustainability checks
        },
        "tgtg": {  # Too Good To Go
            "url": "https://api.toogoodtogo.com/api/v1",
            "key_setting": "TGTG_API_KEY",
            "is_sustainable": True,
        },
        "refurbed": {
            "url": "https://api.refurbed.com/v1",
            "key_setting": "REFURBED_API_KEY",
            "is_sustainable": True,
        },
        "vinted": {
            "url": "https://api.vinted.com/api/v1",
            "key_setting": "VINTED_API_KEY",
            "is_sustainable": True,
        },
        "depop": {
            "url": "https://api.depop.com/api/v1",
            "key_setting": "DEPOP_API_KEY",
            "is_sustainable": True,
        },
        "etsy": {
            "url": "https://openapi.etsy.com/v3",
            "key_setting": "ETSY_API_KEY",
            "is_sustainable": False,  # Requires filtering for eco shops
        },
    }

    def __init__(self, source):
        """Initialize API client for a specific source."""
        if source not in self.SOURCES:
            raise ValueError(f"Unsupported API source: {source}")

        self.source = source
        self.config = self.SOURCES[source]
        self.api_key = getattr(settings, self.config["key_setting"], None)

        if not self.api_key:
            raise ValueError(f"API key missing for {source}")

        self.base_url = self.config["url"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Dealopia/1.0 (sustainable-shopping-app)",
            }
        )

    def fetch_deals(self, limit=100, **params):
        """Fetch deals from the API using the appropriate endpoint."""
        endpoint = self._get_deals_endpoint()

        api_params = {"limit": limit, **params}

        # Add source-specific params
        if self.source == "good_on_you":
            api_params["rating_min"] = 4  # Only good/great rated brands
        elif self.source == "hotukdeals":
            # For HotUKDeals we'll add extra filtering later
            pass
        elif self.source == "etsy":
            api_params["taxonomy_id"] = "sustainable,eco-friendly,organic"

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}", params=api_params
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.RequestException as e:
            logger.error(f"API request error for {self.source}: {str(e)}")
            return []

    def _get_deals_endpoint(self):
        """Get the appropriate endpoint for each source."""
        endpoints = {
            "good_on_you": "brands/deals",
            "hotukdeals": "deals/hot",
            "tgtg": "items",
            "refurbed": "deals",
            "vinted": "items",
            "depop": "products",
            "etsy": "listings/active",
        }
        return endpoints.get(self.source, "deals")

    def _parse_response(self, data):
        """Parse response from different APIs into a standardized format."""
        if not data:
            return []

        # Different APIs have different structures
        if self.source == "good_on_you":
            return self._parse_good_on_you(data)
        elif self.source == "hotukdeals":
            return self._parse_hot_uk_deals(data)
        elif self.source == "tgtg":
            return self._parse_tgtg(data)
        elif self.source == "refurbed":
            return self._parse_refurbed(data)
        elif self.source == "vinted":
            return self._parse_vinted(data)
        elif self.source == "depop":
            return self._parse_depop(data)
        elif self.source == "etsy":
            return self._parse_etsy(data)

        return []

    def _parse_good_on_you(self, data):
        """Parse Good On You API response."""
        standardized_deals = []
        brands = data.get("brands", [])

        for brand in brands:
            # Check for deals with price data
            for product in brand.get("featured_products", []):
                if not all(k in product for k in ("price", "sale_price", "name")):
                    continue

                try:
                    original_price = Decimal(str(product.get("price")))
                    sale_price = Decimal(str(product.get("sale_price")))

                    # Only include actual discounts
                    if sale_price >= original_price:
                        continue

                    discount_percentage = int(
                        ((original_price - sale_price) / original_price) * 100
                    )

                    standardized_deals.append(
                        {
                            "title": product.get("name"),
                            "description": product.get("description", ""),
                            "original_price": original_price,
                            "discounted_price": sale_price,
                            "discount_percentage": discount_percentage,
                            "image_url": product.get("image_url"),
                            "redemption_link": product.get("url"),
                            "shop_name": brand.get("name"),
                            "shop_website": brand.get("website"),
                            "eco_certifications": brand.get("certifications", []),
                            "source": "good_on_you",
                            "external_id": f"goy-{brand.get('id')}-{product.get('id')}",
                            "sustainability_score": self._convert_goy_rating(
                                brand.get("rating", 0)
                            ),
                            "category_names": product.get("categories", []),
                        }
                    )
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error parsing Good On You product: {str(e)}")
                    continue

        return standardized_deals

    def _convert_goy_rating(self, rating):
        """Convert Good On You rating (1-5) to our sustainability score (0-10)."""
        if not rating:
            return 5.0

        # GOY gives ratings 1-5 where 5 is best
        # Convert to our 0-10 scale
        return min(rating * 2, 10)

    def _parse_hot_uk_deals(self, data):
        """Parse HotUKDeals API responses with sustainability filtering."""
        standardized_deals = []
        deals = data.get("deals", [])

        # These keywords help identify potentially sustainable items
        eco_keywords = [
            "eco",
            "sustain",
            "green",
            "organic",
            "fair trade",
            "recycl",
            "reuse",
            "second hand",
            "refurbish",
            "local",
            "carbon neutral",
            "biodegradable",
            "renewable",
        ]

        # These retailers are known to have poor sustainability practices
        excluded_retailers = [
            "temu",
            "shein",
            "aliexpress",
            "wish",
            "romwe",
            "zaful",
            "boohoo",
            "prettylittlething",
        ]

        for deal in deals:
            # Skip deals from retailers with poor sustainability practices
            merchant = deal.get("merchant", {}).get("name", "").lower()
            if any(excluded in merchant for excluded in excluded_retailers):
                continue

            # Check if it's potentially sustainable based on keywords
            title = deal.get("title", "").lower()
            description = deal.get("description", "").lower()

            # Does it contain any sustainability keywords?
            is_potentially_sustainable = any(
                keyword in title or keyword in description for keyword in eco_keywords
            )

            # If not clearly sustainable, skip it
            if not is_potentially_sustainable:
                continue

            try:
                price_data = deal.get("price", {})
                original_price = Decimal(str(price_data.get("original", 0)))
                current_price = Decimal(str(price_data.get("current", 0)))

                if current_price <= 0 or current_price >= original_price:
                    continue

                discount_percentage = int(
                    ((original_price - current_price) / original_price) * 100
                )

                # Calculate basic sustainability score
                sustainability_score = 5.0  # Medium default

                # Adjust score based on keywords found
                keyword_count = sum(
                    keyword in title or keyword in description
                    for keyword in eco_keywords
                )
                sustainability_score += min(keyword_count * 0.5, 3.0)

                standardized_deals.append(
                    {
                        "title": deal.get("title"),
                        "description": deal.get("description", ""),
                        "original_price": original_price,
                        "discounted_price": current_price,
                        "discount_percentage": discount_percentage,
                        "image_url": deal.get("image"),
                        "redemption_link": deal.get("url"),
                        "shop_name": merchant,
                        "shop_website": deal.get("merchant", {}).get("website"),
                        "source": "hotukdeals",
                        "external_id": f"hukd-{deal.get('id')}",
                        "sustainability_score": sustainability_score,
                        "category_names": [
                            deal.get("category", {}).get("name", "Other")
                        ],
                    }
                )
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error parsing HotUKDeals deal: {str(e)}")
                continue

        return standardized_deals

    def _parse_tgtg(self, data):
        """Parse Too Good To Go API response."""
        standardized_deals = []
        items = data.get("items", [])

        for item in items:
            try:
                original_price = Decimal(
                    str(
                        item.get("item", {})
                        .get("price", {})
                        .get("value_including_taxes", 0)
                    )
                )
                current_price = Decimal(
                    str(
                        item.get("item", {})
                        .get("price", {})
                        .get("price_including_taxes", 0)
                    )
                )

                if current_price <= 0 or current_price >= original_price:
                    continue

                discount_percentage = int(
                    ((original_price - current_price) / original_price) * 100
                )

                # Too Good To Go is inherently sustainable (reduces food waste)
                sustainability_score = 8.0

                standardized_deals.append(
                    {
                        "title": item.get("item", {}).get("name"),
                        "description": item.get("item", {}).get("description", ""),
                        "original_price": original_price,
                        "discounted_price": current_price,
                        "discount_percentage": discount_percentage,
                        "image_url": item.get("store", {})
                        .get("logo_picture", {})
                        .get("current_url"),
                        "redemption_link": f"https://toogoodtogo.com/item/{item.get('item', {}).get('item_id')}",
                        "shop_name": item.get("store", {}).get("store_name"),
                        "shop_website": None,
                        "source": "tgtg",
                        "external_id": f"tgtg-{item.get('item', {}).get('item_id')}",
                        "sustainability_score": sustainability_score,
                        "category_names": ["Food", "Anti-Waste"],
                        "local_production": True,
                        "eco_certifications": ["Food Waste Reduction"],
                    }
                )
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error parsing TGTG item: {str(e)}")
                continue

        return standardized_deals

    # Implementation for the remaining API parsers would follow similar patterns
    def _parse_refurbed(self, data):
        """Parse Refurbed API response."""
        standardized_deals = []
        # Implementation would be similar to the ones above
        return standardized_deals

    def _parse_vinted(self, data):
        """Parse Vinted API response."""
        standardized_deals = []
        # Implementation would be similar to the ones above
        return standardized_deals

    def _parse_depop(self, data):
        """Parse Depop API response."""
        standardized_deals = []
        # Implementation would be similar to the ones above
        return standardized_deals

    def _parse_etsy(self, data):
        """Parse Etsy API response."""
        standardized_deals = []
        # Implementation would be similar to the ones above
        return standardized_deals
