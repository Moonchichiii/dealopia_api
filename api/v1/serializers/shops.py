# api/v1/serializers/shops.py
from rest_framework import serializers
from django.utils import timezone

from apps.shops.models import Shop
from api.v1.serializers.categories import CategoryListSerializer


class ShopListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for shop list view with optimized fields
    Used for embedding in other serializers
    """
    category_names = serializers.StringRelatedField(source='categories', many=True, read_only=True)
    deal_count = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = [
            'id', 'name', 'logo', 'logo_url', 'short_description',
            'category_names', 'is_verified', 'is_featured',
            'rating', 'deal_count', 'distance'
        ]
        read_only_fields = ['id', 'is_verified', 'rating', 'distance']
    
    def get_deal_count(self, obj):
        """Get count of active deals"""
        # If deals are prefetched, filter them in Python for better performance
        if hasattr(obj, 'prefetched_deals'):
            now = timezone.now()
            return sum(1 for deal in obj.prefetched_deals 
                      if deal.is_verified and deal.start_date <= now and deal.end_date >= now)
        
        # Otherwise, query the database
        return obj.deals.filter(
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
    
    def get_distance(self, obj):
        """Get distance if annotated"""
        if hasattr(obj, 'distance'):
            # Return distance in kilometers, rounded to 1 decimal place
            return round(obj.distance.km, 1) if obj.distance else None
        return None
    
    def get_logo_url(self, obj):
        """Get full URL for logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class ShopSerializer(ShopListSerializer):
    """
    Full serializer for shop detail view and create/update operations
    """
    categories = CategoryListSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    active_deals = serializers.SerializerMethodField()
    location_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = ShopListSerializer.Meta.fields + [
            'description', 'banner_image', 'website', 'phone', 'email',
            'categories', 'location', 'location_details', 'opening_hours',
            'owner', 'owner_name', 'active_deals', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'rating', 'created_at', 'updated_at', 'owner_name']
    
    def get_owner_name(self, obj):
        """Get the owner's full name"""
        if obj.owner:
            return obj.owner.get_full_name() or obj.owner.email
        return None
    
    def get_active_deals(self, obj):
        """Get active deals for this shop"""
        from api.v1.serializers.deals import DealListSerializer
        
        # Get active deals
        deals = obj.deals.filter(
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by('-is_featured', '-created_at')[:5]
        
        return DealListSerializer(deals, many=True, context=self.context).data
    
    def get_location_details(self, obj):
        """Get location details if available"""
        if obj.location:
            return {
                'address': obj.location.address,
                'city': obj.location.city,
                'state': obj.location.state,
                'country': obj.location.country,
                'postal_code': obj.location.postal_code,
                'latitude': obj.location.point.y if obj.location.point else None,
                'longitude': obj.location.point.x if obj.location.point else None,
            }
        return None
    
    def validate(self, data):
        """Validate shop data"""
        # Ensure opening_hours has a valid structure
        if 'opening_hours' in data:
            if not isinstance(data['opening_hours'], dict):
                raise serializers.ValidationError({
                    'opening_hours': 'Opening hours must be a JSON object'
                })
            
            # Validate each day's hours format
            for day, hours in data['opening_hours'].items():
                if not isinstance(hours, str):
                    raise serializers.ValidationError({
                        'opening_hours': f'Hours for {day} must be a string'
                    })
        
        return data


class ShopCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new shops with validation
    """
    class Meta:
        model = Shop
        fields = [
            'name', 'description', 'short_description',
            'logo', 'banner_image', 'website', 'phone', 'email',
            'categories', 'location', 'opening_hours'
        ]
    
    def create(self, validated_data):
        """Create a new shop and set the current user as owner"""
        user = self.context['request'].user
        validated_data['owner'] = user
        validated_data['is_verified'] = False
        validated_data['rating'] = 0
        
        return super().create(validated_data)