from datetime import timedelta

from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.db.models import Case, Count, DecimalField, F, Q, Value, When
from django.utils import timezone

from apps.categories.models import Category
from apps.products.models import Product
from apps.shops.models import Shop
from core.utils.cache import cache_result, invalidate_cache_prefix


class ProductService:
    """Service for product-related business logic, separating it from views."""

    @staticmethod
    @cache_result(prefix="shop_products", timeout=3600)
    def get_shop_products(shop_id):
        """Get all products for a specific shop"""
        return (
            Product.objects.filter(shop_id=shop_id, is_available=True)
            .select_related("shop")
            .prefetch_related("categories")
        )

    @staticmethod
    def get_products_by_price_range(min_price=None, max_price=None, category_id=None):
        """Get products within a specific price range with optional category filter"""
        queryset = Product.objects.filter(is_available=True)

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if category_id is not None:
            queryset = queryset.filter(categories__id=category_id)

        return queryset.select_related("shop").prefetch_related("categories")

    @staticmethod
    def search_products(search_query, shop_id=None, category_id=None):
        """
        Search products using full-text search capabilities.
        Prioritizes matches in name, then description.
        """
        if not search_query:
            queryset = Product.objects.filter(is_available=True)
        else:
            # Using PostgreSQL full-text search for better results
            vector = SearchVector("name", weight="A") + SearchVector(
                "description", weight="B"
            )
            query = SearchQuery(search_query)

            queryset = (
                Product.objects.annotate(rank=SearchRank(vector, query))
                .filter(rank__gt=0.1, is_available=True)
                .order_by("-rank")
            )

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        return queryset.select_related("shop").prefetch_related("categories").distinct()

    @staticmethod
    @cache_result(prefix="popular_products", timeout=3600)
    def get_popular_products(limit=10, category_id=None, days=30):
        """Get popular products based on view count, purchase count and recency"""
        time_period = timezone.now() - timedelta(days=days)

        queryset = Product.objects.filter(
            created_at__gte=time_period, is_available=True
        )

        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        return (
            queryset.annotate(
                popularity_score=(F("view_count") * 0.6)
                + (F("purchase_count") * 2.5)
                + Case(When(is_featured=True, then=Value(50)), default=Value(0))
            )
            .order_by("-popularity_score")
            .select_related("shop")
            .prefetch_related("categories")[:limit]
        )

    @staticmethod
    def get_shop_products_with_stock(shop_id, min_stock=1, category_id=None):
        """Get products for a specific shop that are in stock"""
        queryset = Product.objects.filter(
            shop_id=shop_id, stock_quantity__gte=min_stock, is_available=True
        )

        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        return queryset.select_related("shop").prefetch_related("categories")

    @staticmethod
    def update_product_stock(product_id, new_quantity):
        """
        Update a product's stock quantity.
        Also updates is_available status based on stock.
        """
        product = Product.objects.get(id=product_id)
        old_quantity = product.stock_quantity
        product.stock_quantity = new_quantity

        if new_quantity <= 0 and product.is_available:
            product.is_available = False
        elif new_quantity > 0 and not product.is_available and old_quantity <= 0:
            product.is_available = True

        product.save(update_fields=["stock_quantity", "is_available", "updated_at"])

        invalidate_cache_prefix(f"product:{product_id}")
        invalidate_cache_prefix(f"shop_products:{product.shop_id}")

        return product

    @staticmethod
    def increment_view_count(product_id):
        """Increment the view count for a product"""
        product = Product.objects.get(id=product_id)
        product.view_count = F("view_count") + 1
        product.save(update_fields=["view_count"])
        product.refresh_from_db()
        return product

    @staticmethod
    def increment_purchase_count(product_id, quantity=1):
        """Increment the purchase count for a product"""
        product = Product.objects.get(id=product_id)
        product.purchase_count = F("purchase_count") + quantity
        product.save(update_fields=["purchase_count"])
        product.refresh_from_db()
        return product

    @staticmethod
    def get_products_for_multiple_shops(shop_ids):
        """Get products from multiple shops"""
        return (
            Product.objects.filter(shop_id__in=shop_ids, is_available=True)
            .select_related("shop")
            .prefetch_related("categories")
        )

    @staticmethod
    def get_related_products(product_id, limit=5):
        """
        Get related products based on shared categories and shop.
        If the product has assigned categories, returns other available products in the same shop
        that share any of those categories. If no categories are assigned, returns other products
        from the same shop (excluding the original).
        """
        from django.db.models import Count, Q

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Product.objects.none()

        category_ids = list(product.categories.values_list("id", flat=True))

        queryset = Product.objects.filter(shop=product.shop, is_available=True).exclude(
            id=product_id
        )

        if category_ids:
            queryset = queryset.filter(categories__in=category_ids)
        # Else, if no categories, we just return other products from the shop.

        queryset = (
            queryset.annotate(
                shared_categories=Count(
                    "categories", filter=Q(categories__in=category_ids)
                )
            )
            .order_by("-shared_categories", "-view_count")
            .select_related("shop")
            .prefetch_related("categories")
            .distinct()[:limit]
        )

        return queryset

    @staticmethod
    def get_featured_products(limit=6, shop_id=None):
        """Get featured products, optionally filtered by shop"""
        queryset = Product.objects.filter(is_featured=True, is_available=True)

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        return (
            queryset.order_by("-updated_at")
            .select_related("shop")
            .prefetch_related("categories")[:limit]
        )

    @staticmethod
    def get_products_with_discounts(min_discount=10, limit=10):
        """Get products with significant discounts"""
        return (
            Product.objects.filter(
                discount_percentage__gte=min_discount, is_available=True
            )
            .order_by("-discount_percentage")
            .select_related("shop")
            .prefetch_related("categories")[:limit]
        )

    @staticmethod
    def get_products_by_category(category_id, limit=None):
        """Get all products in a specific category"""
        queryset = (
            Product.objects.filter(categories__id=category_id, is_available=True)
            .select_related("shop")
            .prefetch_related("categories")
        )

        if limit:
            queryset = queryset[:limit]

        return queryset
