"""Services for deal operations and imports."""

from logging import getLogger
from urllib.parse import urlparse

from cloudinary.uploader import upload
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.utils import timezone

from apps.categories.models import Category
from apps.shops.models import Shop

from .api import EcoRetailerAPI
from .models import Deal

logger = getLogger(__name__)


class DealService:
    """Clean, powerful service for deal operations."""

    @staticmethod
    def get_active_deals(queryset=None):
        """Get active deals with efficient queries."""
        now = timezone.now()

        queryset = queryset or Deal.objects.all()
        return (
            queryset.filter(is_verified=True, start_date__lte=now, end_date__gte=now)
            .select_related("shop")
            .prefetch_related("categories")
        )

    @staticmethod
    def get_featured_deals(limit=6, category_id=None):
        """Get featured deals with caching."""
        cache_key = f"featured_deals:{category_id or 'all'}:{limit}"
        result = cache.get(cache_key)

        if result is None:
            queryset = DealService.get_active_deals().filter(is_featured=True)

            if category_id:
                category_ids = [category_id]
                # Include child categories
                try:
                    category = Category.objects.get(id=category_id)
                    category_ids.extend(category.children.values_list("id", flat=True))
                except Category.DoesNotExist:
                    pass

                queryset = queryset.filter(categories__id__in=category_ids).distinct()

            result = list(
                queryset.order_by("-sustainability_score", "-created_at")[:limit]
            )
            cache.set(cache_key, result, 1800)  # Cache for 30 minutes

        return result

    @staticmethod
    def get_deals_near_location(
        latitude,
        longitude,
        radius_km=10,
        limit=20,
        min_sustainability=None,
        categories=None,
    ):
        """
        Find sustainable deals near a location with optional filters.
        Combines location and sustainability in one optimized query.
        """
        user_location = Point(longitude, latitude, srid=4326)

        # Start with active deals
        queryset = DealService.get_active_deals()

        # Add location filter with distance annotation
        queryset = queryset.filter(
            shop__location__point__dwithin=(user_location, D(km=radius_km))
        ).annotate(distance=Distance("shop__location__point", user_location))

        # Add optional sustainability filter
        if min_sustainability is not None:
            queryset = queryset.filter(sustainability_score__gte=min_sustainability)

        # Add optional category filter
        if categories:
            if not isinstance(categories, (list, tuple)):
                categories = [categories]
            queryset = queryset.filter(categories__id__in=categories).distinct()

        # Custom ordering that balances distance and sustainability
        queryset = queryset.annotate(
            # Weighted score that considers both distance and sustainability
            relevance_score=Case(
                # High sustainability, close by (best)
                When(sustainability_score__gte=8, distance__lte=2, then=Value(1)),
                # High sustainability, medium distance
                When(sustainability_score__gte=8, distance__lte=5, then=Value(2)),
                # Medium sustainability, close by
                When(sustainability_score__gte=5, distance__lte=2, then=Value(3)),
                # High sustainability, further away
                When(sustainability_score__gte=8, then=Value(4)),
                # Medium sustainability, medium distance
                When(sustainability_score__gte=5, distance__lte=5, then=Value(5)),
                # Close by, lower sustainability
                When(distance__lte=2, then=Value(6)),
                # Everything else
                default=Value(7),
                output_field=IntegerField(),
            )
        ).order_by("relevance_score", "distance")

        return queryset[:limit]

    @staticmethod
    def record_interaction(deal_id, interaction_type):
        """Record view or click with atomic update."""
        if interaction_type not in ("view", "click"):
            return False

        field = f"{interaction_type}s_count"

        # Use F() to ensure atomic update
        update_kwargs = {field: F(field) + 1}
        Deal.objects.filter(id=deal_id).update(**update_kwargs)

        return True

    @staticmethod
    def get_related_deals(deal, limit=3):
        """Get related deals using multiple relevance factors."""
        if isinstance(deal, int):
            try:
                deal = Deal.objects.get(id=deal)
            except Deal.DoesNotExist:
                return []

        category_ids = list(deal.categories.values_list("id", flat=True))
        if not category_ids:
            return []

        # Start with active deals excluding the current one
        queryset = DealService.get_active_deals().exclude(id=deal.id)

        # Find deals with matching categories
        queryset = queryset.filter(categories__id__in=category_ids).distinct()

        # Annotate with relevance score for smarter ranking
        queryset = queryset.annotate(
            same_shop=Case(
                When(shop_id=deal.shop_id, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            # Count matching categories
            category_matches=Count(
                "categories", filter=Q(categories__id__in=category_ids)
            ),
        ).order_by("-same_shop", "-category_matches", "-sustainability_score")

        return queryset[:limit]

    @staticmethod
    def get_sustainable_deals(min_score=7.0, limit=10):
        """Get highly sustainable deals."""
        cache_key = f"sustainable_deals:{min_score}:{limit}"
        result = cache.get(cache_key)

        if result is None:
            result = list(
                DealService.get_active_deals()
                .filter(sustainability_score__gte=min_score)
                .order_by("-sustainability_score", "-created_at")[:limit]
            )
            cache.set(cache_key, result, 3600)  # Cache for 1 hour

        return result


class DealImportService:
    """Service for importing deals from various eco-friendly sources."""

    @staticmethod
    def import_from_source(source, limit=100, **params):
        """Import deals from a specific API source."""
        try:
            api_client = EcoRetailerAPI(source)
            deals_data = api_client.fetch_deals(limit, **params)

            return DealImportService.save_deals_data(deals_data)
        except Exception as e:
            logger.error(f"Error importing deals from {source}: {str(e)}")
            return {"success": False, "error": str(e), "created": 0, "updated": 0}

    @staticmethod
    @transaction.atomic
    def save_deals_data(deals_data):
        """Save standardized deals data to the database."""
        created_count = 0
        updated_count = 0

        for deal_data in deals_data:
            try:
                # Get or create shop
                shop_name = deal_data.get("shop_name")
                shop_website = deal_data.get("shop_website")

                if not shop_name:
                    continue

                shop, shop_created = Shop.objects.get_or_create(
                    name=shop_name,
                    defaults={
                        "website": shop_website,
                        "is_verified": True,
                        "short_description": f"Imported from {deal_data.get('source')}",
                    },
                )

                # Get or create categories
                category_names = deal_data.get("category_names", [])
                categories = []

                for name in category_names:
                    if not name:
                        continue

                    category, _ = Category.objects.get_or_create(
                        name=name, defaults={"is_active": True}
                    )
                    categories.append(category)

                # Handle image
                image_url = deal_data.get("image_url")
                if image_url:
                    # Check if the URL is valid
                    parsed_url = urlparse(image_url)
                    if parsed_url.scheme and parsed_url.netloc:
                        # Upload to Cloudinary for optimization
                        try:
                            upload_result = upload(
                                image_url,
                                folder="deals",
                                transformation=[
                                    {"quality": "auto:good"},
                                    {"fetch_format": "auto"},
                                ],
                            )
                            image = upload_result.get("public_id")
                        except Exception as e:
                            logger.warning(
                                f"Error uploading image to Cloudinary: {str(e)}"
                            )
                            image = None
                    else:
                        image = None
                else:
                    image = None

                # Prepare deal data
                deal_fields = {
                    "title": deal_data.get("title"),
                    "description": deal_data.get("description", ""),
                    "original_price": deal_data.get("original_price"),
                    "discounted_price": deal_data.get("discounted_price"),
                    "discount_percentage": deal_data.get("discount_percentage"),
                    "image": image,
                    "start_date": timezone.now(),
                    "end_date": timezone.now()
                    + timezone.timedelta(days=30),  # Default 30 days
                    "redemption_link": deal_data.get("redemption_link", ""),
                    "is_verified": True,
                    "source": deal_data.get("source"),
                    "external_id": deal_data.get("external_id"),
                    "sustainability_score": deal_data.get("sustainability_score", 5.0),
                    "eco_certifications": deal_data.get("eco_certifications", []),
                    "local_production": deal_data.get("local_production", False),
                }

                # Get or update deal
                deal, created = Deal.objects.update_or_create(
                    shop=shop,
                    external_id=deal_data.get("external_id"),
                    defaults=deal_fields,
                )

                # Add categories
                if categories:
                    deal.categories.set(categories)

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                logger.error(f"Error saving deal: {str(e)}, data: {deal_data}")
                continue

        return {
            "success": True,
            "created": created_count,
            "updated": updated_count,
            "total": created_count + updated_count,
        }
