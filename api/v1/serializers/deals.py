from rest_framework import serializers
from apps.deals.models import Deal

class DealSerializer(serializers.ModelSerializer):
    shop_name = serializers.ReadOnlyField(source='shop.name')
    category_names = serializers.StringRelatedField(source='categories', many=True, read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'shop', 'shop_name', 'description', 'original_price',
            'discounted_price', 'discount_percentage', 'categories', 'category_names',
            'image', 'start_date', 'end_date', 'is_featured', 'is_exclusive',
            'is_verified', 'terms_and_conditions', 'coupon_code', 'redemption_link',
            'views_count', 'clicks_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'views_count', 'clicks_count', 'created_at', 'updated_at']
