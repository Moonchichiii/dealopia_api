from rest_framework import serializers
from apps.categories.models import Category


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Category model when used in listings.
    This prevents recursion issues when categories are nested in other objects.
    """
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'icon', 'image', 'is_active'
        ]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'icon', 'image',
            'parent', 'order', 'is_active', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subcategories(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []