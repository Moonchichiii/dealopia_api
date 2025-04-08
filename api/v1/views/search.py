from typing import Dict, List, Optional

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.services import CategoryService
from apps.deals.services import DealService
from apps.shops.services import ShopService
from apps.search.services import GooglePlacesService

class SearchView(APIView):
    """API view for unified search functionality across all entities."""
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name="query", description="Search query", required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name="latitude", description="User latitude", type=OpenApiTypes.FLOAT),
            OpenApiParameter(name="longitude", description="User longitude", type=OpenApiTypes.FLOAT),
            OpenApiParameter(name="radius", description="Search radius in km", type=OpenApiTypes.FLOAT, default=10),
            OpenApiParameter(name="category", description="Category ID", type=OpenApiTypes.INT),
            OpenApiParameter(name="min_sustainability", description="Minimum sustainability score", type=OpenApiTypes.FLOAT, default=0),
            OpenApiParameter(name="include_external", description="Include external sources", type=OpenApiTypes.BOOL, default=True),
        ],
        responses={200: None},
    )
    def get(self, request):
        """Handle GET request for search."""
        try:
            # Extract parameters
            params = self._extract_params(request)
            if isinstance(params, Response):
                return params
                
            query, lat, lng, radius, category_id, min_sustainability, include_external = params
            
            # Build initial response data structure
            data = {
                "query": query,
                "local_results": {"deals": [], "shops": [], "categories": []},
                "external_results": []
            }
            
            # Build filters for deal search
            deals_filter = self._build_deals_filter(
                category_id, min_sustainability, lat, lng, radius
            )
            
            # Perform local database search
            local_deals, local_shops = self._perform_search(
                query, lat, lng, radius, category_id, min_sustainability, deals_filter
            )
            
            # Get categories if query is provided
            if query:
                categories = CategoryService.get_categories_by_name(query)
                data["local_results"]["categories"] = self._serialize_categories(categories)
            
            # Serialize and add local results
            data["local_results"]["deals"] = self._serialize_deals(local_deals)
            data["local_results"]["shops"] = self._serialize_shops(local_shops)
            
            # Add external results if requested (Google Places)
            if include_external and (query or (lat is not None and lng is not None)):
                try:
                    external_results = GooglePlacesService.search(
                        query=query,
                        latitude=lat,
                        longitude=lng,
                        radius_km=radius,
                        min_sustainability=min_sustainability
                    )
                    data["external_results"] = external_results
                except Exception as e:
                    # Log error but don't fail the whole request
                    pass
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _extract_params(self, request):
        """Extract and validate search parameters from the request."""
        try:
            query = request.GET.get("query")
            lat = float(request.GET.get("latitude")) if request.GET.get("latitude") else None
            lng = float(request.GET.get("longitude")) if request.GET.get("longitude") else None
            radius = float(request.GET.get("radius", 10))
            category_id = request.GET.get("category")
            min_sustainability = float(request.GET.get("min_sustainability", 0))
            include_external = request.GET.get("include_external", "true").lower() == "true"
        except ValueError:
            return Response(
                {"error": "Invalid latitude or longitude"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return (query, lat, lng, radius, category_id, min_sustainability, include_external)
    
    def _build_deals_filter(self, category_id, min_sustainability, lat, lng, radius):
        """Build filter dictionary for deals search."""
        filter_dict = {}
        if category_id:
            filter_dict["categories"] = [int(category_id)]
        if min_sustainability > 0:
            filter_dict["min_sustainability"] = min_sustainability
        if lat is not None and lng is not None:
            filter_dict.update({"latitude": lat, "longitude": lng, "radius": radius})
        return filter_dict
    
    def _perform_search(self, query, lat, lng, radius, category_id, min_sustainability, deals_filter):
        """Perform search across deals and shops."""
        local_deals = []
        local_shops = []
        
        # Search by query if provided
        if query:
            local_deals.extend(DealService.search_deals(query, deals_filter))
            local_shops.extend(ShopService.search_shops(query, category_id))
        
        # Search by location if coordinates provided
        if lat is not None and lng is not None:
            location_deals = DealService.get_deals_near_location(
                lat, lng, radius_km=radius, min_sustainability=min_sustainability
            )
            
            # Avoid duplicates
            existing_deal_ids = {d.id for d in local_deals}
            for deal in location_deals:
                if deal.id not in existing_deal_ids:
                    local_deals.append(deal)
            
            location_shops = ShopService.get_shops_by_location(lat, lng, radius_km=radius)
            
            # Avoid duplicates
            existing_shop_ids = {s.id for s in local_shops}
            for shop in location_shops:
                if shop.id not in existing_shop_ids:
                    local_shops.append(shop)
        
        return local_deals, local_shops
    
    def _serialize_deals(self, deals) -> List[Dict]:
        """Serialize deal objects to dictionary representation."""
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
                "image": deal.image.url if hasattr(deal.image, "url") else None,
                "end_date": deal.end_date,
            }
            for deal in deals
        ]
    
    def _serialize_shops(self, shops) -> List[Dict]:
        """Serialize shop objects to dictionary representation."""
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "description": shop.short_description,
                "logo": shop.logo.url if shop.logo else None,
                "distance": float(shop.distance.km) if getattr(shop, "distance", None) else None,
                "website": shop.website,
                "rating": float(shop.rating),
            }
            for shop in shops
        ]
    
    def _serialize_categories(self, categories) -> List[Dict]:
        """Serialize category objects to dictionary representation."""
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "image": cat.image.url if cat.image else None,
                "deal_count": getattr(cat, "deal_count", None),
            }
            for cat in categories
        ]