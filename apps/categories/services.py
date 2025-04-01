from django.db.models import Count, Q

from .models import Category


class CategoryService:
    """Service for category-related business logic, separating it from views."""

    @staticmethod
    def get_active_categories(queryset=None):
        """Return only active categories."""
        queryset = queryset or Category.objects.all()
        return queryset.filter(is_active=True)

    @staticmethod
    def get_root_categories():
        """Get top-level categories."""
        return CategoryService.get_active_categories().filter(parent=None)

    @staticmethod
    def get_categories_with_subcategories():
        """Get hierarchical categories structure with nested subcategories."""
        root_categories = CategoryService.get_root_categories().order_by("order")

        result = []
        for category in root_categories:
            subcategories = (
                CategoryService.get_active_categories()
                .filter(parent=category)
                .order_by("order")
            )

            category_data = {
                "id": category.id,
                "name": category.name,
                "image": category.image.url if category.image else None,
                "description": category.description,
                "subcategories": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "image": sub.image.url if sub.image else None,
                        "description": sub.description,
                    }
                    for sub in subcategories
                ],
            }
            result.append(category_data)

        return result

    @staticmethod
    def get_categories_with_deal_counts():
        """Get categories with the count of active deals for each."""
        from apps.deals.services import DealService

        active_deals = DealService.get_active_deals()

        return (
            CategoryService.get_active_categories()
            .annotate(deal_count=Count("deals", filter=Q(deals__in=active_deals)))
            .order_by("-deal_count", "order")
        )

    @staticmethod
    def get_popular_categories(limit=6):
        """Get categories with most active deals."""
        categories = CategoryService.get_categories_with_deal_counts()
        return categories.filter(deal_count__gt=0)[:limit]

    @staticmethod
    def get_category_breadcrumbs(category_id):
        """Get category breadcrumb path from root to the specified category."""
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return []

        breadcrumbs = [{"id": category.id, "name": category.name}]

        parent = category.parent
        while parent:
            breadcrumbs.insert(0, {"id": parent.id, "name": parent.name})
            parent = parent.parent

        return breadcrumbs
