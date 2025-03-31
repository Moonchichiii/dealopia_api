from django.contrib.gis.geos import Point
from rest_framework import serializers

from apps.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source="latitude", read_only=True)
    longitude = serializers.FloatField(source="longitude", read_only=True)

    class Meta:
        model = Location
        fields = [
            "id",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _process_coordinates(self, data):
        """Create Point object if coordinates are provided in the request"""
        lat = data.get("latitude")
        lng = data.get("longitude")

        if lat and lng:
            try:
                return Point(float(lng), float(lat), srid=4326)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"coordinates": "Invalid latitude or longitude values"})
        return None

    def create(self, validated_data):
        point = self._process_coordinates(self.context["request"].data)
        if point:
            validated_data["point"] = point
        return super().create(validated_data)

    def update(self, instance, validated_data):
        point = self._process_coordinates(self.context["request"].data)
        if point:
            validated_data["point"] = point
        return super().update(instance, validated_data)
