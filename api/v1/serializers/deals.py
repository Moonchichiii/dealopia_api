from django.utils import timezone
from rest_framework import serializers

from api.v1.serializers.categories import CategoryListSerializer
from api.v1.serializers.shops import ShopListSerializer
from apps.deals.models import Deal


class DealListSerializer(serializers.ModelSerializer):
    """Serializer for deal list view with optimized fields"""
    shop_name = serializers.ReadOnlyField(source='shop.name')
    shop_logo = serializers.SerializerMethodField()
    category_names = serializers.StringRelatedField(source='categories', many=True, read_only=True)
    discount_amount = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'shop', 'shop_name', 'shop_logo',
            'original_price', 'discounted_price', 'discount_percentage',
            'discount_amount', 'categories', 'category_names', 'image',
            'start_date', 'end_date', 'is_featured', 'is_exclusive',
            'is_verified', 'time_left', 'is_new', 'coupon_code',
        ]
        read_only_fields = ['id', 'time_left', 'is_new']
    
    def get_shop_logo(self, obj):
        return obj.shop.logo.url if obj.shop.logo else None
        
    def get_discount_amount(self, obj):
        """Calculate the discount amount in currency"""
        if obj.original_price and obj.discounted_price:
            return obj.original_price - obj.discounted_price
        return None
    
    def get_time_left(self, obj):
        """Return the time left until the deal expires"""
        if not obj.end_date:
            return None
            
        now = timezone.now()
        if now > obj.end_date:
            return "Expired"
            
        time_left = obj.end_date - now
        days = time_left.days
        
        if days > 0:
            return f"{days} days"
        
        hours = time_left.seconds // 3600
        if hours > 0:
            return f"{hours} hours"
            
        minutes = (time_left.seconds % 3600) // 60
        return f"{minutes} minutes"
    
    def get_is_new(self, obj):
        """Check if the deal is new (less than 3 days old)"""
        return (timezone.now() - obj.created_at).days < 3 if obj.created_at else False


class DealSerializer(DealListSerializer):
    """Serializer for deal create/update with validation"""
    
    def validate(self, data):
        """Validate the deal data"""
        # Ensure discounted_price is lower than original_price
        if 'original_price' in data and 'discounted_price' in data:
            if data['discounted_price'] >= data['original_price']:
                raise serializers.ValidationError(
                    "Discounted price must be lower than the original price"
                )
        
        # Validate dates
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
            
            if data['end_date'] < timezone.now():
                raise serializers.ValidationError(
                    "End date cannot be in the past"
                )
        
        # Calculate discount_percentage if not provided
        if ('original_price' in data and 
            'discounted_price' in data and 
            'discount_percentage' not in data):
            discount = ((data['original_price'] - data['discounted_price']) / 
                       data['original_price']) * 100
            data['discount_percentage'] = round(discount)
        
        return data


class DealDetailSerializer(DealSerializer):
    """Detailed serializer for single deal view"""
    shop = ShopListSerializer(read_only=True)
    categories = CategoryListSerializer(many=True, read_only=True)
    similar_deals = serializers.SerializerMethodField()
    
    class Meta(DealSerializer.Meta):
        fields = DealSerializer.Meta.fields + [
            'description', 'terms_and_conditions', 'redemption_link',
            'views_count', 'clicks_count', 'created_at', 'updated_at',
            'similar_deals'
        ]
    
    def get_similar_deals(self, obj):
        """Get a few similar deals based on categories"""
        from apps.deals.services import DealService
        
        similar = DealService.get_related_deals(obj, limit=3)
        return DealListSerializer(similar, many=True, context=self.context).data
