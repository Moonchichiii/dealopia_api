from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.categories.services import CategoryService
from apps.deals.models import Deal
from apps.locations.models import Location
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_superuser(
        email="admin@example.com", password="AdminPass123!"
    )
    return user


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def parent_category():
    return Category.objects.create(
        name="Parent Category",
        description="Parent category description",
        is_active=True,
        order=1,
    )


@pytest.fixture
def child_category(parent_category):
    return Category.objects.create(
        name="Child Category",
        description="Child category description",
        parent=parent_category,
        is_active=True,
        order=1,
    )


@pytest.fixture
def shop(admin_user):
    location = Location.objects.create(city="Test City", country="Test Country")
    shop = Shop.objects.create(
        name="Test Shop",
        owner=admin_user,
        description="Shop description",
        short_description="Short description",
        email="shop@example.com",
        location=location,
        is_verified=True,
    )
    return shop


@pytest.fixture
def deal(shop, child_category):
    deal = Deal.objects.create(
        title="Test Deal",
        shop=shop,
        description="Deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        is_verified=True,
    )
    deal.categories.add(child_category)
    return deal


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_creation(self, parent_category, child_category):
        assert parent_category.id is not None
        assert parent_category.name == "Parent Category"
        assert parent_category.parent is None

        assert child_category.id is not None
        assert child_category.name == "Child Category"
        assert child_category.parent == parent_category

    def test_category_str_representation(self, parent_category):
        assert str(parent_category) == "Parent Category"

    def test_category_ordering(self):
        category1 = Category.objects.create(name="Category 1", order=3)
        category2 = Category.objects.create(name="Category 2", order=1)
        category3 = Category.objects.create(name="Category 3", order=2)

        categories = Category.objects.all().order_by("order")

        assert categories[0] == category2  # order=1
        assert categories[1] == category3  # order=2
        assert categories[2] == category1  # order=3


@pytest.mark.django_db
class TestCategoryService:
    def test_get_active_categories(self, parent_category, child_category):
        inactive_category = Category.objects.create(
            name="Inactive Category", is_active=False
        )

        active_categories = CategoryService.get_active_categories()

        assert parent_category in active_categories
        assert child_category in active_categories
        assert inactive_category not in active_categories

    def test_get_root_categories(self, parent_category, child_category):
        root_categories = CategoryService.get_root_categories()

        assert parent_category in root_categories
        assert child_category not in root_categories

    def test_get_categories_with_subcategories(self, parent_category, child_category):
        result = CategoryService.get_categories_with_subcategories()

        parent_data = next(
            (item for item in result if item["id"] == parent_category.id), None
        )

        assert parent_data is not None
        assert parent_data["name"] == parent_category.name
        assert len(parent_data["subcategories"]) == 1
        assert parent_data["subcategories"][0]["id"] == child_category.id

    def test_get_popular_categories(self, child_category, deal):
        popular_categories = CategoryService.get_popular_categories()

        assert child_category in popular_categories

    def test_get_category_breadcrumbs(self, parent_category, child_category):
        breadcrumbs = CategoryService.get_category_breadcrumbs(child_category.id)

        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["id"] == parent_category.id
        assert breadcrumbs[0]["name"] == parent_category.name
        assert breadcrumbs[1]["id"] == child_category.id
        assert breadcrumbs[1]["name"] == child_category.name

        breadcrumbs = CategoryService.get_category_breadcrumbs(parent_category.id)
        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]["id"] == parent_category.id

        breadcrumbs = CategoryService.get_category_breadcrumbs(999)
        assert len(breadcrumbs) == 0


@pytest.mark.django_db
class TestCategoryAPI:
    def test_list_categories(self, api_client, parent_category, child_category):
        url = reverse("category-list")
        response = api_client.get(url, format="json")

        assert response.status_code == status.HTTP_200_OK

        data = response.data.get("results", response.data)
        assert len(data) >= 2

        category_ids = [item["id"] for item in data]
        assert parent_category.id in category_ids
        assert child_category.id in category_ids

    def test_retrieve_category(self, api_client, parent_category):
        url = reverse("category-detail", args=[parent_category.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == parent_category.id
        assert response.data["name"] == parent_category.name
        assert response.data["description"] == parent_category.description

    def test_create_category(self, authenticated_admin_client):
        url = reverse("category-list")
        data = {
            "name": "New Category",
            "description": "New category description",
            "is_active": True,
            "order": 5,
        }

        response = authenticated_admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Category"

        category = Category.objects.get(id=response.data["id"])
        assert category.name == "New Category"
        assert category.description == "New category description"
        assert category.order == 5

    def test_create_child_category(self, authenticated_admin_client, parent_category):
        url = reverse("category-list")
        data = {
            "name": "New Child Category",
            "description": "New child description",
            "parent": parent_category.id,
            "is_active": True,
        }

        response = authenticated_admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Child Category"
        assert response.data["parent"] == parent_category.id

    def test_category_deals_endpoint(self, api_client, child_category, deal):
        url = reverse("category-deals", args=[child_category.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id
        assert response.data[0]["title"] == deal.title

    def test_featured_categories_endpoint(self, api_client, child_category, deal):
        url = reverse("category-featured")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        category_ids = [item["id"] for item in response.data]
        assert child_category.id in category_ids
