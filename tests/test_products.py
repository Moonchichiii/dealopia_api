"""
Tests for the products app.
"""
import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# Import our fixtures
from tests.fixtures import user, location, category, shop, api_client, authenticated_client, deal

from apps.products.models import Product
from apps.products.services import ProductService
from apps.shops.models import Shop

User = get_user_model()


@pytest.fixture
def product(shop):
    """Create a test product associated with a shop"""
    return Product.objects.create(
        shop=shop,
        name="Test Product",
        description="Test product description",
        price=Decimal("29.99"),
        stock_quantity=100,
    )


@pytest.fixture
def second_user():
    """Create a second user for permission testing"""
    return User.objects.create_user(
        email="seconduser@example.com", password="AnotherStrongPass123!"
    )


@pytest.fixture
def second_user_client(api_client, second_user):
    """API client authenticated with the second user"""
    api_client.force_authenticate(user=second_user)
    return api_client


@pytest.mark.django_db
class TestProductModel:
    def test_product_creation(self, product):
        """Test that a product can be created with the correct attributes"""
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.shop.name == "Test Shop"
        assert product.price == Decimal("29.99")
        assert product.stock_quantity == 100

    def test_product_string_representation(self, product):
        """Test the string representation of the product"""
        assert str(product) == "Test Product (Test Shop)"

    def test_product_shop_relationship(self, product, shop):
        """Test the relationship between product and shop"""
        assert product.shop == shop
        assert product in shop.products.all()

    def test_shop_products_relationship(self, shop, product):
        """Test that we can get all products for a shop"""
        # Add another product to the shop
        second_product = Product.objects.create(
            shop=shop,
            name="Second Product",
            description="Another test product",
            price=Decimal("19.99"),
            stock_quantity=50,
        )

        # Get products from shop
        shop_products = shop.products.all()
        
        assert shop_products.count() == 2
        assert product in shop_products
        assert second_product in shop_products


@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, api_client, product):
        """Test listing all products"""
        url = reverse("product-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

        # Find our product in the response
        product_data = next(
            (item for item in response.data if item["id"] == product.id), None
        )
        assert product_data is not None
        assert product_data["name"] == product.name
        assert Decimal(product_data["price"]) == product.price

    def test_retrieve_product(self, api_client, product):
        """Test retrieving a specific product"""
        url = reverse("product-detail", args=[product.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == product.name
        assert response.data["description"] == product.description
        assert Decimal(response.data["price"]) == product.price
        assert response.data["shop"] == product.shop.id

    def test_create_product_shop_owner(self, authenticated_client, shop):
        """Test that a shop owner can create a product for their shop"""
        url = reverse("product-list")
        data = {
            "shop": shop.id,
            "name": "New Product",
            "description": "New product description",
            "price": "39.99",
            "stock_quantity": 200,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Product"
        assert Decimal(response.data["price"]) == Decimal("39.99")
        assert response.data["shop"] == shop.id

        # Verify in database
        product = Product.objects.get(id=response.data["id"])
        assert product.name == "New Product"
        assert product.shop == shop

    def test_filter_products_by_shop(self, api_client, product, shop):
        """Test filtering products by shop"""
        # Create another shop and product
        other_user = User.objects.create_user(
            email="other@example.com", password="password123"
        )
        other_shop = Shop.objects.create(
            name="Other Shop",
            owner=other_user,
            description="Other shop description",
            short_description="Other shop",
            email="other@shop.com",
            location=shop.location,  # Reuse location for simplicity
            is_verified=True,
        )
        
        other_product = Product.objects.create(
            shop=other_shop,
            name="Other Product",
            description="Product from another shop",
            price=Decimal("15.99"),
            stock_quantity=30,
        )

        # Get products filtered by original shop
        url = reverse("product-list")
        response = api_client.get(url, {"shop": shop.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == product.id

        # Get products filtered by other shop
        response = api_client.get(url, {"shop": other_shop.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == other_product.id


@pytest.mark.django_db
class TestProductService:
    def test_get_shop_products(self, shop, product):
        """Test getting all products for a shop"""
        # Add another product to the shop
        second_product = Product.objects.create(
            shop=shop,
            name="Second Product",
            description="Another test product",
            price=Decimal("19.99"),
            stock_quantity=50,
        )
        
        # Get products using service
        shop_products = ProductService.get_shop_products(shop.id)
        
        assert shop_products.count() == 2
        assert product in shop_products
        assert second_product in shop_products

    def test_get_products_by_price_range(self, shop):
        """Test filtering products by price range"""
        # Create products with different prices
        product1 = Product.objects.create(
            shop=shop,
            name="Cheap Product",
            price=Decimal("9.99"),
            stock_quantity=10,
        )
        
        product2 = Product.objects.create(
            shop=shop,
            name="Mid-range Product",
            price=Decimal("49.99"),
            stock_quantity=10,
        )
        
        product3 = Product.objects.create(
            shop=shop,
            name="Expensive Product",
            price=Decimal("99.99"),
            stock_quantity=10,
        )
        
        # Test minimum price only
        results = ProductService.get_products_by_price_range(min_price=Decimal("40.00"))
        assert product1 not in results
        assert product2 in results
        assert product3 in results
        
        # Test maximum price only
        results = ProductService.get_products_by_price_range(max_price=Decimal("50.00"))
        assert product1 in results
        assert product2 in results
        assert product3 not in results
        
        # Test price range
        results = ProductService.get_products_by_price_range(
            min_price=Decimal("40.00"),
            max_price=Decimal("70.00")
        )
        assert product1 not in results
        assert product2 in results
        assert product3 not in results

    def test_update_product_stock(self, product):
        """Test updating a product's stock quantity"""
        # Initial stock quantity is 100
        assert product.stock_quantity == 100
        
        # Update stock quantity
        updated_product = ProductService.update_product_stock(product.id, 75)
        
        # Check updated product
        assert updated_product.id == product.id
        assert updated_product.stock_quantity == 75
        
        # Verify in database
        product.refresh_from_db()
        assert product.stock_quantity == 75

    def test_get_related_products(self, shop, product):
        """Test getting related products from the same shop"""
        # Create several more products in the same shop
        related_products = []
        for i in range(1, 6):
            related_products.append(
                Product.objects.create(
                    shop=shop,
                    name=f"Related Product {i}",
                    description=f"Related product {i} description",
                    price=Decimal(f"{10+i}.99"),
                    stock_quantity=10,
                )
            )
            
        # Get related products
        results = ProductService.get_related_products(product.id, limit=3)
        
        # Should return 3 products
        assert results.count() == 3
        
        # Should not include the original product
        assert product not in results
        
        # All products should be from the same shop
        for result in results:
            assert result.shop == shop


@pytest.mark.django_db
class TestShopProductIntegration:
    def test_shop_products_relationship(self, shop, product):
        """Test shop-product relationship in both directions"""
        # Create additional product for the shop
        second_product = Product.objects.create(
            shop=shop,
            name="Second Product",
            description="Another product description",
            price=Decimal("15.99"),
            stock_quantity=25,
        )
        
        # Test shop.products relationship
        assert shop.products.count() == 2
        assert product in shop.products.all()
        assert second_product in shop.products.all()
        
        # Test product.shop relationship
        assert product.shop == shop
        assert second_product.shop == shop

    def test_product_creation_via_api(self, authenticated_client, shop):
        """Test creating a product for a shop via the API"""
        url = reverse("product-list")
        data = {
            "shop": shop.id,
            "name": "New Product via API",
            "description": "Product created through API",
            "price": "45.99",
            "stock_quantity": 100,
        }
        
        response = authenticated_client.post(url, data)
        
        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Product via API"
        assert response.data["shop"] == shop.id
        
        # Verify product was created and associated with the shop
        product_id = response.data["id"]
        product = Product.objects.get(id=product_id)
        assert product.shop == shop
        assert product in shop.products.all()

    def test_shop_with_products_deletion(self, shop, product):
        """Test that deleting a shop cascades to its products"""
        # Create additional product for the shop
        second_product = Product.objects.create(
            shop=shop,
            name="Second Product",
            price=Decimal("15.99"),
            stock_quantity=25,
        )
        
        product_ids = [product.id, second_product.id]
        
        # Delete the shop
        shop.delete()
        
        # Verify products were deleted (cascade)
        for product_id in product_ids:
            assert not Product.objects.filter(id=product_id).exists()

    def test_shop_products_listing_api(self, api_client, shop, product):
        """Test listing products filtered by shop via API"""
        # Create additional products for this shop
        for i in range(3):
            Product.objects.create(
                shop=shop,
                name=f"Extra Product {i+1}",
                price=Decimal(f"{10+i}.99"),
                stock_quantity=10,
            )
            
        # Create another shop with its own products
        other_shop = shop.__class__.objects.create(
            name="Other Shop",
            owner=shop.owner,  # Same owner for simplicity
            description="Other shop description",
            short_description="Other shop",
            email="other@shop.com",
            location=shop.location,  # Reuse location for simplicity
            is_verified=True,
        )
        
        # Create products for other shop
        for i in range(2):
            Product.objects.create(
                shop=other_shop,
                name=f"Other Shop Product {i+1}",
                price=Decimal(f"{20+i}.99"),
                stock_quantity=10,
            )
            
        # Get products for original shop
        url = reverse("product-list")
        response = api_client.get(url, {"shop": shop.id})
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4  # Original product + 3 extras
        
        # All products should belong to the original shop
        for product_data in response.data:
            assert product_data["shop"] == shop.id
            
        # Get products for other shop
        response = api_client.get(url, {"shop": other_shop.id})
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # 2 products in other shop
        
        # All products should belong to the other shop
        for product_data in response.data:
            assert product_data["shop"] == other_shop.id