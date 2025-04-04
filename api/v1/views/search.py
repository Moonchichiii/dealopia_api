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
            OpenApiParameter(name="query", description="Search query", required=False, type=str),
            OpenApiParameter(name="latitude", description="User latitude", type=float),
            OpenApiParameter(name="longitude", description="User longitude", type=float),
            OpenApiParameter(name="radius", description="Search radius in km", type=float, default=10),
            OpenApiParameter(name="category", description="Category ID", type=int),
            OpenApiParameter(name="min_sustainability", description="Minimum sustainability score", type=float, default=0),
            OpenApiParameter(name="include_external", description="Include external sources", type=bool, default=True),
        ],
        responses={200: None}  # A detailed response schema can be defined here.
    )
    def get(self, request):
        # Extract and validate query parameters
        params = self._extract_query_params(request)
        if isinstance(params, Response):
            return params
            
        query, latitude, longitude, radius, category_id, min_sustainability, include_external = params
        
        # Initialize response data structure
        data = {
            "query": query,
            "local_results": {
                "deals": [],
                "shops": [],
                "categories": []
            },
            "external_results": []
        }
        
        # Build filters for search queries
        deals_filter = self._build_deals_filter(category_id, min_sustainability, latitude, longitude, radius)
        
        # Perform searches
        local_deals, local_shops = self._perform_searches(
            query, latitude, longitude, radius, category_id, min_sustainability, deals_filter
        )
        
        # Get category results if query provided
        if query:
            categories = CategoryService.get_categories_by_name(query)
            data["local_results"]["categories"] = self._serialize_categories(categories)
        
        # Serialize results
        data["local_results"]["deals"] = self._serialize_deals(local_deals)
        data["local_results"]["shops"] = self._serialize_shops(local_shops)
        
        # Include external results if requested
        if include_external and (query or (latitude and longitude)):
            data["external_results"] = ScraperService.search_external_sources(query, latitude, longitude, radius)
        
        return Response(data)
    
    def _extract_query_params(self, request):
        """Extract and validate query parameters from the request."""
        query = request.GET.get("query")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")
        radius = float(request.GET.get("radius", 10))
        category_id = request.GET.get("category")
        min_sustainability = float(request.GET.get("min_sustainability", 0))
        include_external = request.GET.get("include_external", "true").lower() == "true"
        
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return Response(
                    {"error": "Invalid latitude or longitude"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return query, latitude, longitude, radius, category_id, min_sustainability, include_external
    
    def _build_deals_filter(self, category_id, min_sustainability, latitude, longitude, radius):
        """Build filter dictionary for deal searches."""
        deals_filter = {}
        if category_id:
            deals_filter["categories"] = [int(category_id)]
        if min_sustainability > 0:
            deals_filter["min_sustainability"] = min_sustainability
        if latitude and longitude:
            deals_filter["latitude"] = latitude
            deals_filter["longitude"] = longitude
            deals_filter["radius"] = radius
        return deals_filter
    
    def _perform_searches(self, query, latitude, longitude, radius, category_id, min_sustainability, deals_filter):
        """Perform search operations based on provided parameters."""
        local_deals = []
        local_shops = []
        
        # Text-based search
        if query:
            text_deals = DealService.search_deals(query, deals_filter)
            local_deals.extend(text_deals)
            
            text_shops = ShopService.search_shops(query, category_id)
            local_shops.extend(text_shops)
        
        # Location-based search
        if latitude and longitude:
            location_deals = DealService.get_deals_near_location(
                latitude, longitude, radius_km=radius, min_sustainability=min_sustainability
            )
            
            # Add unique location deals
            existing_deal_ids = {deal.id for deal in local_deals}
            for deal in location_deals:
                if deal.id not in existing_deal_ids:
                    local_deals.append(deal)
                    existing_deal_ids.add(deal.id)
            
            # Add unique location shops
            location_shops = ShopService.get_shops_by_location(latitude, longitude, radius_km=radius)
            existing_shop_ids = {shop.id for shop in local_shops}
            for shop in location_shops:
                if shop.id not in existing_shop_ids:
                    local_shops.append(shop)
                    existing_shop_ids.add(shop.id)
        
        return local_deals, local_shops
    
    def _serialize_deals(self, deals) -> List[Dict]:
        """Serialize deal objects to dictionary format."""
        return [
            {
                "id": deal.id,
                "title": deal.title,
                "shop_name": deal.shop.name,
                "original_price": float(deal.original_price),
                "discounted_price": float(deal.discounted_price),
                "discount_percentage": deal.discount_percentage,
                "sustainability_score": float(deal.sustainability_score),
                "distance": float(deal.distance.km) if getattr(deal, "distance", None) else None,
            }
            for deal in deals
        ]
    
    def _serialize_shops(self, shops) -> List[Dict]:
        """Serialize shop objects to dictionary format."""
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "description": shop.short_description,
                "distance": float(shop.distance.km) if getattr(shop, "distance", None) else None,
            }
            for shop in shops
        ]
    
    def _serialize_categories(self, categories) -> List[Dict]:
        """Serialize category objects to dictionary format."""
        return [
            {
                "id": category.id,
                "name": category.name,
                "deal_count": getattr(category, "deal_count", None),
            }
            for category in categories
        ]
