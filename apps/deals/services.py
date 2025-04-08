"""Service methods for deal-related operations."""

import logging
from typing import List, Optional, Union

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db.models import (Case, Count, F, IntegerField, Q, QuerySet, Value,
                              When)
from django.utils import timezone

from apps.deals.models import Deal
from apps.shops.models import Shop

logger = logging.getLogger(__name__)


class DealService:
    @staticmethod
    def get_active_deals(queryset: Optional[QuerySet] = None) -> QuerySet:
        """Returns deals that are currently valid (is_verified=True, within start/end date)."""
        now = timezone.now()
        queryset = queryset or Deal.objects.all()
        return (
            queryset.filter(is_verified=True, start_date__lte=now, end_date__gte=now)
            .select_related("shop")
            .prefetch_related("categories")
        )

    @staticmethod
    def search_deals(query: str = None, filters: dict = None) -> QuerySet:
        """Filters deals by text, categories, or lat/lng if provided."""
        try:
            queryset = DealService.get_active_deals()
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query)
                    | Q(description__icontains=query)
                    | Q(shop__name__icontains=query)
                    | Q(categories__name__icontains=query)
                ).distinct()

            if filters:
                # filter by categories
                if "categories" in filters and filters["categories"]:
                    queryset = queryset.filter(categories__id__in=filters["categories"])

                # filter by user location
                if all(k in filters for k in ["latitude", "longitude"]):
                    lat, lng = filters["latitude"], filters["longitude"]
                    radius = filters.get("radius", 10)
                    user_location = Point(float(lng), float(lat), srid=4326)

                    queryset = queryset.filter(
                        shop__location__coordinates__dwithin=(
                            user_location,
                            D(km=radius),
                        )
                    ).annotate(
                        distance=Distance("shop__location__coordinates", user_location)
                    )

                # filter by min sustainability
                if "min_sustainability" in filters:
                    queryset = queryset.filter(
                        sustainability_score__gte=filters["min_sustainability"]
                    )

            return queryset.order_by("-sustainability_score", "-created_at")

        except Exception as e:
            logger.error(f"Error in deal search: {str(e)}", exc_info=True)
            return Deal.objects.none()

    @staticmethod
    def get_deals_near_location(
        latitude: float,
        longitude: float,
        radius_km: float = 10,
        limit: int = 20,
        min_sustainability: Optional[float] = None,
        categories: Optional[Union[int, List[int]]] = None,
    ) -> QuerySet:
        """Return deals near a specific lat/lng within radius_km, optionally filtered."""
        try:
            # validate lat/lng
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                logger.warning(f"Invalid coordinates: lat={latitude}, lng={longitude}")
                return Deal.objects.none()

            radius_km = max(0.1, min(radius_km, 50))
            limit = max(1, min(limit, 100))

            user_location = Point(float(longitude), float(latitude), srid=4326)

            queryset = (
                DealService.get_active_deals()
                .filter(
                    shop__location__coordinates__dwithin=(
                        user_location,
                        D(km=radius_km),
                    )
                )
                .annotate(
                    distance=Distance("shop__location__coordinates", user_location)
                )
            )

            if min_sustainability is not None:
                queryset = queryset.filter(sustainability_score__gte=min_sustainability)

            if categories:
                # handle single int or list of ints
                category_list = (
                    [categories] if isinstance(categories, int) else categories
                )
                queryset = queryset.filter(categories__id__in=category_list).distinct()

            queryset = queryset.annotate(
                relevance_score=Case(
                    When(sustainability_score__gte=8, distance__lte=2, then=Value(1)),
                    When(sustainability_score__gte=8, distance__lte=5, then=Value(2)),
                    When(sustainability_score__gte=5, distance__lte=2, then=Value(3)),
                    When(sustainability_score__gte=8, then=Value(4)),
                    When(sustainability_score__gte=5, distance__lte=5, then=Value(5)),
                    When(distance__lte=2, then=Value(6)),
                    default=Value(7),
                    output_field=IntegerField(),
                )
            ).order_by("relevance_score", "distance")

            return queryset[:limit]

        except Exception as e:
            logger.error(
                f"Error in nearby deals location search: {str(e)}", exc_info=True
            )
            return Deal.objects.none()

    @staticmethod
    def get_local_and_sustainable_deals(
        latitude: float,
        longitude: float,
        radius_km: float = 100,
        min_score: float = 5.0,
    ) -> QuerySet:
        """Return deals that are both local (within radius_km) and meet a min sustainability score."""
        try:
            user_location = Point(float(longitude), float(latitude), srid=4326)

            queryset = (
                DealService.get_active_deals()
                .filter(
                    shop__location__coordinates__dwithin=(
                        user_location,
                        D(km=radius_km),
                    )
                )
                .annotate(
                    distance=Distance("shop__location__coordinates", user_location)
                )
                .filter(sustainability_score__gte=min_score)
                .order_by("-sustainability_score", "distance")
            )
            return queryset

        except Exception as e:
            logger.error(
                f"Error fetching local and sustainable deals: {str(e)}", exc_info=True
            )
            return Deal.objects.none()

    @staticmethod
    def record_interaction(deal_id: int, interaction_type: str) -> bool:
        """Increment a 'views_count' or 'clicks_count' field in Deal."""
        try:
            if interaction_type not in ("view", "click"):
                logger.warning(f"Invalid interaction type: {interaction_type}")
                return False

            field = f"{interaction_type}s_count"
            Deal.objects.filter(id=deal_id).update(**{field: F(field) + 1})
            return True
        except Exception as e:
            logger.error(
                f"Error recording {interaction_type} interaction: {str(e)}",
                exc_info=True,
            )
            return False

    @staticmethod
    def get_related_deals(deal: Union[int, Deal], limit: int = 3) -> QuerySet:
        """Return deals that share categories or shop with the given deal."""
        try:
            if isinstance(deal, int):
                deal = Deal.objects.get(id=deal)

            category_ids = list(deal.categories.values_list("id", flat=True))
            if not category_ids:
                return Deal.objects.none()

            queryset = DealService.get_active_deals().exclude(id=deal.id)
            queryset = queryset.filter(categories__id__in=category_ids).distinct()

            queryset = queryset.annotate(
                same_shop=Case(
                    When(shop_id=deal.shop_id, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                category_matches=Count(
                    "categories", filter=Q(categories__id__in=category_ids)
                ),
            ).order_by("-same_shop", "-category_matches", "-sustainability_score")

            return queryset[:limit]

        except Exception as e:
            logger.error(f"Error fetching related deals: {str(e)}", exc_info=True)
            return Deal.objects.none()

    @staticmethod
    def get_sustainable_deals(min_score: float = 7.0, limit: int = 10) -> List[Deal]:
        """Return top deals with sustainability_score >= min_score, using cache for performance."""
        try:
            cache_key = f"sustainable_deals:{min_score}:{limit}"
            result = cache.get(cache_key)

            if result is None:
                result = list(
                    DealService.get_active_deals()
                    .filter(sustainability_score__gte=min_score)
                    .order_by("-sustainability_score", "-created_at")[:limit]
                )
                cache.set(cache_key, result, 3600)

            return result

        except Exception as e:
            logger.error(f"Error fetching sustainable deals: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_deals_by_category(category_id: int, limit: int = 10) -> QuerySet:
        """Return deals belonging to a certain category."""
        return Deal.objects.filter(categories__id=category_id, is_verified=True)[:limit]

    @staticmethod
    def get_featured_deals(limit=6, category_id=None) -> QuerySet:
        """Return a set of featured deals, optionally filtered by category."""
        queryset = DealService.get_active_deals().filter(is_featured=True)
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset.order_by("-created_at")[:limit]

    @staticmethod
    def get_deals_by_multiple_categories(
        category_ids: List[int], limit: int = 10
    ) -> List[Deal]:
        """Get deals that belong to any of the provided categories, sorted by relevance."""
        if not category_ids:
            return []

        try:
            queryset = (
                DealService.get_active_deals()
                .filter(categories__id__in=category_ids)
                .distinct()
            )

            queryset = queryset.annotate(
                category_match_count=Count(
                    "categories", filter=Q(categories__id__in=category_ids)
                )
            )

            queryset = queryset.order_by("-category_match_count", "-created_at")

            return list(queryset[:limit])

        except Exception as e:
            logger.error(
                f"Error getting deals by multiple categories: {str(e)}", exc_info=True
            )
            return []

    @staticmethod
    def get_ending_soon_deals(days=3, limit=10):
        """Get deals that are ending soon."""
        now = timezone.now()
        end_date_threshold = now + timezone.timedelta(days=days)

        return (
            DealService.get_active_deals()
            .filter(end_date__lte=end_date_threshold)
            .order_by("end_date")[:limit]
        )

    @staticmethod
    def find_sustainable_deals_for_search(
        query=None, latitude=None, longitude=None, radius_km=10
    ):
        """Find sustainable deals based on search query and/or location."""
        from apps.scrapers.services import ScraperService

        results = {"local_deals": [], "external_deals": []}

        # First, search local database
        local_deals = []

        # If we have a query, search by text
        if query:
            local_deals = DealService.search_deals(
                query, filters={"min_sustainability": 5.0}
            )

        # If we have location, add location-based search
        if latitude is not None and longitude is not None:
            location_deals = DealService.get_deals_near_location(
                latitude, longitude, radius_km=radius_km, min_sustainability=5.0
            )

            # Combine with text search results, ensuring no duplicates
            if query:
                existing_ids = {deal.id for deal in local_deals}
                for deal in location_deals:
                    if deal.id not in existing_ids:
                        local_deals.append(deal)
            else:
                local_deals = location_deals

        # Convert deals to dictionary format
        results["local_deals"] = [
            {
                "id": deal.id,
                "title": deal.title,
                "shop_name": deal.shop.name,
                "original_price": float(deal.original_price),
                "discounted_price": float(deal.discounted_price),
                "discount_percentage": deal.discount_percentage,
                "sustainability_score": float(deal.sustainability_score),
                "image": deal.image.url if hasattr(deal.image, "url") else None,
                "distance": getattr(deal, "distance", None),
                "source": "database",
            }
            for deal in local_deals
        ]

        # Next, supplement with external search
        if len(results["local_deals"]) < 5:
            external_results = ScraperService.search_external_sources(
                query=query, latitude=latitude, longitude=longitude, radius_km=radius_km
            )

            results["external_deals"] = ScraperService.process_external_results(
                external_results
            )

        return results
