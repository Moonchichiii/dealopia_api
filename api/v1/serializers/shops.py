from rest_framework import serializers
from backend.apps.shops.models import Shop
from backend.apps.categories.models import Category

class ShopSerializer(serializers.ModelSerializer):
    category_names = serializers.StringRelatedField(source='categories', many=True, read_only=True)
    deal_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'id', 'name', 'owner', 'description', 'short_description',
            'logo', 'banner_image', 'website', 'phone', 'email',
            'categories', 'category_names', 'location', 'is_verified',
            'is_featured', 'rating', 'opening_hours', 'deal_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'rating', 'created_at', 'updated_at']
    
    def get_deal_count(self, obj):
        return obj.deals.count()
