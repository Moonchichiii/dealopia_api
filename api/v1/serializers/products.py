from rest_framework import serializers
from django.utils import timezone

from apps.products.models import Product
from api.v1.serializers.categories import CategoryListSerializer
from api.v1.serializers.shops import ShopListSerializer


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for listing products with essential information"""
    shop_name = serializers.StringRelatedField(source="shop")
    category_names = serializers.StringRelatedField(source="categories", many=True, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "shop",
            "shop_name",
            "price",
            "discount_percentage",
            "discounted_price",
            "discount_amount",
            "image",
            "image_url",
            "category_names",
            "is_featured",
            "is_available",
            "stock_quantity",
        ]
        read_only_fields = ["id", "discounted_price", "discount_amount"]
        
    def get_image_url(self, obj):
        if not obj.image:
            return None
            
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class ProductSerializer(ProductListSerializer):
    """Detailed serializer for product creation and detailed view"""
    shop = ShopListSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(
        source="shop",
        queryset=Product._meta.get_field("shop").related_model.objects.all(),
        write_only=True
    )
    categories = CategoryListSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source="categories",
        queryset=Product._meta.get_field("categories").related_model.objects.all(),
        write_only=True,
        many=True,
        required=False
    )
    active_deals = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ProductListSerializer.Meta.fields + [
            "shop_id",
            "categories",
            "category_ids",
            "description",
            "barcode",
            "additional_images",
            "dimensions",
            "weight",
            "weight_unit",
            "specifications",
            "view_count",
            "purchase_count",
            "active_deals",
            "created_at",
            "updated_at",
            "meta_title",
            "meta_description",
        ]
        read_only_fields = ["id", "view_count", "purchase_count", "created_at", "updated_at"]
        
    def get_active_deals(self, obj):
        """Get active deals for this product"""
        from api.v1.serializers.deals import DealListSerializer
        
        deals = obj.get_active_deals()
        if not deals.exists():
            return []
            
        return DealListSerializer(deals, many=True, context=self.context).data
        
    def create(self, validated_data):
        """Handle creation with nested relationships"""
        categories = validated_data.pop('categories', [])
        instance = super().create(validated_data)
        
        if categories:
            instance.categories.set(categories)
            
        return instance
        
    def update(self, instance, validated_data):
        """Handle updates with nested relationships"""
        categories = validated_data.pop('categories', None)
        instance = super().update(instance, validated_data)
        
        if categories is not None:
            instance.categories.set(categories)
            
        return instance
        
    def validate(self, data):
        """Validate discount percentage and dimensions"""
        discount_percentage = data.get('discount_percentage')
        
        if discount_percentage is not None and (discount_percentage < 0 or discount_percentage > 100):
            raise serializers.ValidationError({
                "discount_percentage": "Discount percentage must be between 0 and 100"
            })
            
        dimensions = data.get('dimensions')
        if dimensions:
            required_keys = ['length', 'width', 'height']
            missing_keys = [key for key in required_keys if key not in dimensions]
            
            if missing_keys:
                raise serializers.ValidationError({
                    "dimensions": f"Missing required keys: {', '.join(missing_keys)}"
                })
                
            for key in required_keys:
                if not isinstance(dimensions.get(key), (int, float)):
                    raise serializers.ValidationError({
                        "dimensions": f"Value for {key} must be a number"
                    })
                    
        return data


class ProductBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating products"""
    shop_id = serializers.IntegerField(required=True)
    category_id = serializers.IntegerField(required=False)
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    price_change_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2,
        required=False
    )
    operation = serializers.ChoiceField(
        choices=['increase', 'decrease'],
        default='increase',
        required=False
    )
    is_available = serializers.BooleanField(required=False)
    
    def validate(self, data):
        """Validate required fields for different operations"""
        if 'price_change_percentage' in data and 'operation' in data:
            # If updating prices, need percentage
            if data['price_change_percentage'] <= 0:
                raise serializers.ValidationError({
                    "price_change_percentage": "Must be greater than 0"
                })
        elif 'is_available' in data:
            # If updating availability, need is_available
            pass
        else:
            raise serializers.ValidationError(
                "Either price_change_percentage or is_available is required"
            )
        
        return data