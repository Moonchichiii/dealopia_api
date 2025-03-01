from rest_framework import serializers
from backend.apps.locations.models import Location

class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'address', 'city', 'state', 'country',
            'postal_code', 'point', 'latitude', 'longitude',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_latitude(self, obj):
        return obj.point.y if obj.point else None
    
    def get_longitude(self, obj):
        return obj.point.x if obj.point else None
