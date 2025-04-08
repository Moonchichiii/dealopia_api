from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.deals.tasks import (clean_expired_deals, send_deal_notifications,
                              update_deal_statistics,
                              update_sustainability_scores, warm_deal_caches)
from apps.locations.models import Location
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="testuser@example.com", password="StrongPass123!"
    )


@pytest.fixture
def location():
    return Location.objects.create(
        city="Test City", country="Test Country", coordinates=Point(0, 0)
    )


@pytest.fixture
def shop(user, location):
    return Shop.objects.create(
        name="Test Shop",
        owner=user,
        description="Test shop description",
        short_description="Test shop",
        email="shop@example.com",
        website="https://example.com",
        location=location,
        rating=4.5,
        is_verified=True,
    )


@pytest.fixture
def category():
    return Category.objects.create(
        name="Test Category", description="Test category description"
    )


@pytest.fixture
def deal(shop, category):
    deal_obj = Deal.objects.create(
        title="Test Deal",
        shop=shop,
        description="Test deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("80.00"),
        discount_percentage=20,
        start_date=timezone.now() - timedelta(days=1),
        end_date=timezone.now() + timedelta(days=7),
        sustainability_score=8.0,
        is_verified=True,
    )
    deal_obj.categories.add(category)
    return deal_obj


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestDealAPI:
    def test_list_deals(self, api_client, deal):
        url = reverse("deal-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["results"], list)
        assert len(response.data["results"]) > 0
        assert response.data["results"][0]["title"] == deal.title

    def test_retrieve_deal(self, api_client, deal):
        url = reverse("deal-detail", args=[deal.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == deal.title
        assert response.data["shop"]["name"] == deal.shop.name
        assert Decimal(response.data["original_price"]) == deal.original_price

    def test_create_deal(self, authenticated_client, shop, category):
        url = reverse("deal-list")
        data = {
            "title": "New Deal",
            "shop": shop.id,
            "description": "New deal description",
            "original_price": "120.00",
            "discounted_price": "90.00",
            "discount_percentage": 25,
            "start_date": (timezone.now() - timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timedelta(days=7)).isoformat(),
            "categories": [category.id],
            "is_verified": True,
            "image": "https://example.com/test-image.jpg",
        }
        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_featured_deals_endpoint(self, api_client, deal):
        deal.is_featured = True
        deal.save()
        url = reverse("deal-featured")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == deal.id

    def test_sustainable_deals_endpoint(self, api_client, deal):
        url = reverse("deal-sustainable")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == deal.id

        url_with_param = f"{url}?min_score=9.0"
        response = api_client.get(url_with_param)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


@pytest.mark.django_db
class TestDealModel:
    def test_deal_creation(self, deal):
        assert deal.id is not None
        assert deal.title == "Test Deal"
        assert deal.original_price == Decimal("100.00")
        assert deal.discount_percentage == 20
        assert deal.is_active is True

    def test_is_active_property(self, shop):
        active_deal = Deal.objects.create(
            title="Active Deal",
            shop=shop,
            description="Description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_verified=True,
        )
        assert active_deal.is_active is True

        expired_deal = Deal.objects.create(
            title="Expired Deal",
            shop=shop,
            description="Description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=1),
            is_verified=True,
        )
        assert expired_deal.is_active is False

    def test_discount_amount_property(self, deal):
        assert deal.discount_amount == Decimal("20.00")


@pytest.mark.django_db
class TestDealService:
    def test_get_active_deals(self, deal):
        active_deals = DealService.get_active_deals()
        assert deal in active_deals

        deal.end_date = timezone.now() - timedelta(days=1)
        deal.save()
        active_deals = DealService.get_active_deals()
        assert deal not in active_deals

    def test_search_deals(self, deal):
        results = DealService.search_deals("Test Deal")
        assert deal in results

        results = DealService.search_deals("Nonexistent")
        assert deal not in results

    def test_get_sustainable_deals(self, deal):
        sustainable_deals = DealService.get_sustainable_deals(min_score=3.0)
        assert deal in sustainable_deals

        sustainable_deals = DealService.get_sustainable_deals(min_score=9.0)
        assert deal not in sustainable_deals


@pytest.mark.django_db
class TestDealTasks:
    @pytest.fixture
    def task_shop(self, django_user_model, db):
        user = django_user_model.objects.create_user(
            email="shopowner@example.com", password="Test123!"
        )
        location = Location.objects.create(
            city="Test City", country="Test Country", coordinates=Point(0, 0)
        )
        return Shop.objects.create(
            name="Test Shop",
            owner=user,
            description="A test shop",
            short_description="Test Shop",
            email="shop@example.com",
            website="https://example.com",
            location=location,
            is_verified=True,
        )

    @pytest.fixture
    def active_deal_task(self, task_shop):
        deal = Deal.objects.create(
            title="Active Deal",
            shop=task_shop,
            description="Active deal description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("80.00"),
            discount_percentage=20,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
            sustainability_score=8.0,
            is_verified=True,
        )
        return deal

    @pytest.fixture
    def expired_deal_task(self, task_shop):
        deal = Deal.objects.create(
            title="Expired Deal",
            shop=task_shop,
            description="Expired deal description",
            original_price=Decimal("100.00"),
            discounted_price=Decimal("70.00"),
            discount_percentage=30,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            sustainability_score=8.0,
            is_verified=True,
        )
        return deal

    def test_clean_expired_deals(self, task_shop, active_deal_task, expired_deal_task):
        result = clean_expired_deals(days=30)
        assert result["deleted"] == 1
        assert active_deal_task in Deal.objects.all()
        assert expired_deal_task not in Deal.objects.all()

    def test_update_sustainability_scores(self, active_deal_task):
        active_deal_task.sustainability_score = 0
        active_deal_task.save()
        result = update_sustainability_scores()
        assert result["updated"] >= 1
        active_deal_task.refresh_from_db()
        assert active_deal_task.sustainability_score > 0

    def test_send_deal_notifications_success(
        self, active_deal_task, category, django_user_model
    ):
        active_deal_task.categories.clear()
        active_deal_task.categories.add(category)
        result = send_deal_notifications(active_deal_task.id)
        assert result["success"] is True

    def test_update_deal_statistics(self, active_deal_task):
        active_deal_task.views_count = 100
        active_deal_task.clicks_count = 20
        active_deal_task.save()
        result = update_deal_statistics()
        assert result["updated"] >= 1

    def test_warm_deal_caches(self):
        result = warm_deal_caches()
        assert result["success"] is True
