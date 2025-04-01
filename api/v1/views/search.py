"""
Search API endpoint for finding deals across multiple sources.
Leverages external real-world APIs for a unified search experience.
"""

from typing import Dict, List, Optional, Any

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.deals.services import DealService
from apps.shops.services import ShopService
from apps.locations.services import LocationService
from apps.categories.services import CategoryService
from apps.scrapers.services import ScraperService


class SearchView(APIView):
    """
    API endpoint for searching local and external data sources.
    Provides a unified search experience across deals, shops, and categories.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="query", description="Search query", required=True, type=str),
            OpenApiParameter(name="latitude", description="User latitude", type=float),
            OpenApiParameter(name="longitude", description="User longitude", type=float),
            OpenApiParameter(name="radius", description="Search radius in km", type=float, default=10),
            OpenApiParameter(name="category", description="Category ID", type=int),
            OpenApiParameter(name="min_sustainability", description="Minimum sustainability score", type=float, default=0),
            OpenApiParameter(name="include_external", description="Include external sources", type=bool, default=True),
        ],
        responses={200: None}  # You may define a more detailed response schema here.
    )
    def get(self, request):
        """
        Handle GET requests for search functionality.
        """
        query = request.GET.get("query")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")
        radius = float(request.GET.get("radius", 10))
        category_id = request.GET.get("category")
        min_sustainability = float(request.GET.get("min_sustainability", 0))
        include_external = request.GET.get("include_external", "true").lower() == "true"

        # Convert latitude and longitude to float if provided
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return Response(
                    {"error": "Invalid latitude or longitude"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        data = {
            "query": query,
            "local_results": {
                "deals": [],
                "shops": [],
                "categories": []
            },
            "external_results": []
        }

        # Local search using our internal services
        if query:
            deals_filter = {}
            if category_id:
                deals_filter["categories"] = [int(category_id)]
            if min_sustainability > 0:
                deals_filter["min_sustainability"] = min_sustainability
            if latitude and longitude:
                deals_filter["latitude"] = latitude
                deals_filter["longitude"] = longitude
                deals_filter["radius"] = radius

            deals = DealService.search_deals(query, deals_filter)
            data["local_results"]["deals"] = self._serialize_deals(deals)

            shops = ShopService.search_shops(query, category_id)
            if latitude and longitude:
                shops = ShopService.get_shops_by_location(latitude, longitude, radius_km=radius)
            data["local_results"]["shops"] = self._serialize_shops(shops)

            categories = CategoryService.get_categories_by_name(query)
            data["local_results"]["categories"] = self._serialize_categories(categories)

        elif latitude and longitude:
            # Location-only search without a text query
            nearby_deals = DealService.get_deals_near_location(
                latitude, longitude, radius_km=radius, min_sustainability=min_sustainability
            )
            data["local_results"]["deals"] = self._serialize_deals(nearby_deals)
            nearby_shops = ShopService.get_shops_by_location(latitude, longitude, radius_km=radius)
            data["local_results"]["shops"] = self._serialize_shops(nearby_shops)
            data["local_results"]["categories"] = []  # Or implement location-specific category retrieval

        # External search using the Crawlbase account via our scraper service
        if include_external and (query or (latitude and longitude)):
            external_results = ScraperService.search_external_sources(query, latitude, longitude, radius)
            data["external_results"] = external_results

        return Response(data)

    def _serialize_deals(self, deals) -> List[Dict]:
        """Serialize deal objects for the API response."""
        return [
            {
                "id": deal.id,
                "title": deal.title,
                "shop_name": deal.shop.name,
                "original_price": float(deal.original_price),
                "discounted_price": float(deal.discounted_price),
                "discount_percentage": deal.discount_percentage,
                "sustainability_score": float(deal.sustainability_score),
                "distance": getattr(deal, "distance", None),
            }
            for deal in deals
        ]

    def _serialize_shops(self, shops) -> List[Dict]:
        """Serialize shop objects for the API response."""
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "description": shop.short_description,
                "distance": getattr(shop, "distance", None),
            }
            for shop in shops
        ]

    def _serialize_categories(self, categories) -> List[Dict]:
        """Serialize category objects for the API response."""
        return [
            {
                "id": category.id,
                "name": category.name,
                "deal_count": getattr(category, "deal_count", None),
            }
            for category in categories
        ]
