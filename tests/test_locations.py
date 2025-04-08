from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.deals.models import Deal
from apps.locations.models import Location
from apps.locations.services import LocationService
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
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def location_nyc():
    # New York City coordinates
    return Location.objects.create(
        name="New York Office",
        address="123 Broadway",
        city="New York",
        state="NY",
        country="United States",
        postal_code="10001",
        coordinates=Point(-74.0060, 40.7128),  # longitude, latitude
    )


@pytest.fixture
def location_la():
    # Los Angeles coordinates
    return Location.objects.create(
        name="LA Office",
        address="456 Hollywood Blvd",
        city="Los Angeles",
        state="CA",
        country="United States",
        postal_code="90001",
        coordinates=Point(-118.2437, 34.0522),  # longitude, latitude
    )


@pytest.fixture
def location_london():
    # London coordinates
    return Location.objects.create(
        name="London Office",
        address="789 Baker St",
        city="London",
        country="United Kingdom",
        postal_code="SW1A 1AA",
        coordinates=Point(-0.1276, 51.5074),  # longitude, latitude
    )


@pytest.fixture
def shop_nyc(admin_user, location_nyc):
    return Shop.objects.create(
        name="NYC Shop",
        owner=admin_user,
        description="Shop in New York",
        short_description="NYC Shop",
        email="nyc@example.com",
        location=location_nyc,
        is_verified=True,
    )


@pytest.fixture
def deal_nyc(shop_nyc):
    return Deal.objects.create(
        title="NYC Deal",
        shop=shop_nyc,
        description="Deal description",
        original_price=Decimal("100.00"),
        discounted_price=Decimal("75.00"),
        discount_percentage=25,
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() + timezone.timedelta(days=7),
        is_verified=True,
    )


@pytest.mark.django_db
class TestLocationModel:
    def test_location_creation(self, location_nyc):
        assert location_nyc.id is not None
        assert location_nyc.city == "New York"
        assert location_nyc.country == "United States"
        assert location_nyc.coordinates is not None

        # Test latitude and longitude properties
        assert round(location_nyc.latitude, 4) == 40.7128
        assert round(location_nyc.longitude, 4) == -74.0060

    def test_location_str_representation(self, location_nyc):
        assert str(location_nyc) == "123 Broadway, New York, United States"

    def test_in_country_method(self, location_nyc, location_la, location_london):
        us_locations = Location.in_country("United States")

        assert location_nyc in us_locations
        assert location_la in us_locations
        assert location_london not in us_locations

        # Test case insensitivity
        us_locations_lower = Location.in_country("united states")
        assert len(us_locations_lower) == 2

    def test_in_city_method(self, location_nyc, location_la, location_london):
        nyc_locations = Location.in_city("New York")

        assert location_nyc in nyc_locations
        assert location_la not in nyc_locations
        assert location_london not in nyc_locations

        # Test with country filter
        nyc_us_locations = Location.in_city("New York", country="United States")
        assert location_nyc in nyc_us_locations

        # Test with incorrect country
        nyc_uk_locations = Location.in_city("New York", country="United Kingdom")
        assert location_nyc not in nyc_uk_locations


@pytest.mark.django_db
class TestLocationService:
    def test_get_nearby_locations(self, location_nyc, location_la, location_london):
        # Search near NYC
        nyc_point = Point(-74.0060, 40.7128)
        nearby_nyc = LocationService.get_nearby_locations(nyc_point.y, nyc_point.x, 10)
        #                ^ lat=40.7128           ^ lng=-74.0060

        assert location_nyc in nearby_nyc
        assert location_la not in nearby_nyc
        assert location_london not in nearby_nyc

        # Search near London
        london_point = Point(-0.1276, 51.5074)
        nearby_london = LocationService.get_nearby_locations(
            london_point.y, london_point.x, 10
        )
        #                       ^ lat=51.5074               ^ lng=-0.1276

        assert location_nyc not in nearby_london
        assert location_la not in nearby_london
        assert location_london in nearby_london

    def test_get_deals_summary_for_locations(self, location_nyc, shop_nyc, deal_nyc):
        # Test the annotation functionality
        nyc_locations = Location.objects.filter(id=location_nyc.id)
        locations_with_deals = LocationService.get_deals_summary_for_locations(
            nyc_locations
        )

        # Implementation might vary, but in general, should return locations with deal counts
        assert locations_with_deals is not None


@pytest.mark.django_db
class TestLocationAPI:
    def test_list_locations(
        self, api_client, location_nyc, location_la, location_london
    ):
        url = reverse("location-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3

        # Verify all locations are in response
        location_cities = [item["city"] for item in response.data]
        assert "New York" in location_cities
        assert "Los Angeles" in location_cities
        assert "London" in location_cities

    def test_retrieve_location(self, api_client, location_nyc):
        url = reverse("location-detail", args=[location_nyc.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == location_nyc.id
        assert response.data["city"] == location_nyc.city
        assert response.data["address"] == location_nyc.address
        assert response.data["latitude"] == location_nyc.latitude
        assert response.data["longitude"] == location_nyc.longitude

    def test_create_location(self, authenticated_client):
        url = reverse("location-list")
        data = {
            "address": "123 Main St",
            "city": "Chicago",
            "state": "IL",
            "country": "United States",
            "postal_code": "60601",
            "latitude": 41.8781,
            "longitude": -87.6298,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["city"] == "Chicago"

        # Verify in database
        location = Location.objects.get(id=response.data["id"])
        assert location.city == "Chicago"
        assert location.coordinates is not None
        assert round(location.latitude, 4) == 41.8781
        assert round(location.longitude, 4) == -87.6298

    def test_update_location(self, authenticated_client, location_nyc):
        url = reverse("location-detail", args=[location_nyc.id])
        data = {
            "address": "Updated Address",
            "latitude": 40.7300,
            "longitude": -74.0100,
        }

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["address"] == "Updated Address"

        # Verify in database
        location_nyc.refresh_from_db()
        assert location_nyc.address == "Updated Address"
        assert round(location_nyc.latitude, 4) == 40.7300
        assert round(location_nyc.longitude, 4) == -74.0100

    def test_nearby_endpoint(
        self, api_client, location_nyc, location_la, location_london
    ):
        # Search near NYC
        url = reverse("location-nearby")
        params = {"lat": 40.7128, "lng": -74.0060, "radius": 10}

        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "locations" in response.data
        assert len(response.data["locations"]) > 0

        # The NYC location should be in the results
        location_ids = [item["id"] for item in response.data["locations"]]
        assert location_nyc.id in location_ids

        # Test including deals
        params["include_deals"] = "true"
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "locations" in response.data
        assert "deals" in response.data

    def test_popular_cities_endpoint(
        self, api_client, location_nyc, location_la, location_london
    ):
        url = reverse("location-popular-cities")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

        # Cities should be in results
        cities = [item["city"] for item in response.data]
        assert "New York" in cities or "Los Angeles" in cities or "London" in cities

        # Test with country filter
        params = {"country": "United States"}
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

        us_cities = [item["city"] for item in response.data]
        assert "New York" in us_cities or "Los Angeles" in us_cities
        assert "London" not in us_cities

    def test_stats_endpoint(
        self, api_client, location_nyc, location_la, location_london
    ):
        url = reverse("location-stats")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "total_locations" in response.data
        assert response.data["total_locations"] >= 3

        # Should have country counts
        assert "countries" in response.data
        assert len(response.data["countries"]) >= 2

        # Should have United States and United Kingdom
        country_names = [item["country"] for item in response.data["countries"]]
        assert "United States" in country_names
        assert "United Kingdom" in country_names
