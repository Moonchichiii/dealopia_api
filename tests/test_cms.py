import datetime
from decimal import Decimal
import pytest
import cloudinary
import unittest.mock as mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from apps.shops.models import Shop
from apps.products.models import Product
from apps.deals.models import Deal
from apps.cms.models.images import CloudinaryImage, CloudinaryRendition

# -------------------------------------------------------------------
# Cloudinary Configuration & Patching
# -------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_cloudinary():
    """Configure Cloudinary for testing with dummy values."""
    cloudinary.config(
        cloud_name="test_cloud_name",
        api_key="test_api_key",
        api_secret="test_api_secret"
    )

@pytest.fixture(autouse=True)
def mock_cloudinary_upload():
    """
    Patch Cloudinary's upload_resource (used in CloudinaryImage.pre_save)
    and patch CloudinaryImage.get_rendition to return a dummy rendition.
    """
    # Patch globally where the uploader is used.
    with mock.patch('cloudinary.uploader.upload_resource') as mock_upload_resource:
        mock_upload_resource.return_value = {
            'public_id': 'test_public_id',
            'version': '1234567890',
            'signature': 'test_signature',
            'width': 500,
            'height': 500,
            'format': 'jpg',
            'resource_type': 'image',
            'created_at': '2025-04-07T15:00:00Z',
            'url': 'https://res.cloudinary.com/test_cloud_name/image/upload/test_public_id',
            'secure_url': 'https://res.cloudinary.com/test_cloud_name/image/upload/test_public_id',
        }
        # Also patch get_rendition so that it always returns a dummy rendition.
        with mock.patch('apps.cms.models.images.CloudinaryImage.get_rendition') as mock_get_rendition:
            rendition = CloudinaryRendition()
            rendition.file = 'https://res.cloudinary.com/test_cloud_name/image/upload/test_public_id'
            mock_get_rendition.return_value = rendition
            yield mock_upload_resource

# -------------------------------------------------------------------
# User, Shop, and Related Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def user_data():
    return {
        "email": "cmsadmin@dealopia.com",
        "password": "TestPass123!",
        "first_name": "CMS",
        "last_name": "Admin"
    }

@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        email="superadmin@dealopia.com",
        password="SuperSecurePass123!"
    )

@pytest.fixture
def shop_owner(django_user_model):
    return django_user_model.objects.create_user(
        email="shopowner@dealopia.com",
        password="ShopOwnerPass123!"
    )

# Fixture for the Location required by the Shop model.
@pytest.fixture
def test_location():
    from apps.locations.models import Location
    return Location.objects.create(
        address="123 Test St",
        city="Test City",
        country="Test Country",
        postal_code="12345"
    )

@pytest.fixture
def test_shop(shop_owner, test_location):
    return Shop.objects.create(
        name="Sustainable Goods Shop",
        owner=shop_owner,
        description="Eco-friendly products",
        sustainability_score=8.5,
        location=test_location
    )

# Create a tiny 1x1 pixel GIF image in memory.
@pytest.fixture
def test_image():
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x01\x0A\x00\x01\x00\x2C\x00'
        b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    )
    return SimpleUploadedFile(
        name='test_image.gif',
        content=image_content,
        content_type='image/gif'
    )

@pytest.fixture
def test_product(test_shop):
    return Product.objects.create(
        name="Eco Friendly Product",
        shop=test_shop,
        price=29.99,
        is_available=True,
        sustainability_score=7.5
    )

# -------------------------------------------------------------------
# Test Classes
# -------------------------------------------------------------------

@pytest.mark.django_db
class TestCMSCloudinaryImage:
    def test_cloudinary_image_creation(self, test_image):
        # Pass transformation_options as a dict (Django JSONField handles dict conversion)
        cloudinary_image = CloudinaryImage.objects.create(
            file=test_image,
            title='Test Sustainable Product Image',
            transformation_options={
                'quality': 'auto',
                'width': 500,
                'crop': 'limit'
            }
        )
        assert cloudinary_image.file.public_id is not None
        assert cloudinary_image.title == 'Test Sustainable Product Image'

    def test_cloudinary_image_rendition(self, test_image):
        cloudinary_image = CloudinaryImage.objects.create(
            file=test_image,
            title='Rendition Test Image'
        )
        rendition_specs = ['width-300', 'height-200', 'crop-fill']
        for spec in rendition_specs:
            rendition = cloudinary_image.get_rendition(spec)
            assert isinstance(rendition, CloudinaryRendition)
            assert rendition.url is not None
            assert rendition.url.startswith('https://res.cloudinary.com')

@pytest.mark.django_db
class TestCMSAdminAccess:
    def test_superuser_cms_access(self, client, superuser):
        client.login(email=superuser.email, password="SuperSecurePass123!")
        response = client.get(reverse('wagtailadmin_home'))
        assert response.status_code == status.HTTP_200_OK

    def test_shop_owner_cms_access(self, client, shop_owner, test_product):
        client.login(email=shop_owner.email, password="ShopOwnerPass123!")
        preview_url = reverse('cms:product-cms-preview', kwargs={'pk': test_product.id})
        response = client.get(preview_url)
        assert response.status_code == status.HTTP_200_OK
        preview_data = response.json()
        assert preview_data['product']['name'] == 'Eco Friendly Product'
        assert 'related_products' in preview_data

@pytest.mark.django_db
class TestCMSAPIEndpoints:
    def test_wagtail_api_endpoints(self, client, superuser):
        client.login(email=superuser.email, password="SuperSecurePass123!")
        # According to config/urls.py, the Wagtail API router is mounted at /api/wagtail/
        api_endpoints = [
            '/api/wagtail/pages/',
            '/api/wagtail/images/',
            '/api/wagtail/documents/'
        ]
        for endpoint in api_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK

    def test_cms_dashboard_preview(self, client, superuser, test_shop):
        client.login(email=superuser.email, password="SuperSecurePass123!")
        from django.utils import timezone
        now = timezone.now()
        Deal.objects.create(
            title='Sustainable Deal',
            shop=test_shop,
            discount_percentage=20,
            original_price=Decimal("100.00"),
            discounted_price=Decimal("80.00"),
            start_date=now,
            end_date=now + datetime.timedelta(days=7)
    )
        preview_url = reverse('cms:shop-cms-preview', kwargs={'pk': test_shop.id})
        response = client.get(preview_url)
        assert response.status_code == status.HTTP_200_OK
        preview_data = response.json()
        assert preview_data['shop']['name'] == 'Sustainable Goods Shop'
        assert 'deals' in preview_data
        assert 'products' in preview_data

@pytest.mark.django_db
class TestCMSPermissions:
    def test_shop_owner_limited_access(self, client, shop_owner, test_shop):
        client.login(email=shop_owner.email, password="ShopOwnerPass123!")
        another_user = User.objects.create_user(
            email="another@example.com",
            password="AnotherPass123!"
        )
        another_shop = Shop.objects.create(
            name="Another Shop",
            owner=another_user,
            description="Unrelated shop",
            location=test_shop.location
        )
        preview_url = reverse('shop-cms-preview', kwargs={'pk': another_shop.id})
        response = client.get(preview_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_cms_configuration(settings):
    assert settings.WAGTAIL_SITE_NAME == "Dealopia Admin"
    assert settings.WAGTAILIMAGES_IMAGE_MODEL == "cms.CloudinaryImage"
    assert settings.WAGTAILAPI_BASE_URL == "/api/cms"
    assert settings.WAGTAILAPI_LIMIT_MAX == 100
