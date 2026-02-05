from django.contrib.gis.geos import Point
from rest_framework import serializers

from apps.locations.models import Location


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model with readable/writable lat/long fields."""

    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "coordinates",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create location and set coordinates if lat/long are provided."""
        lat = validated_data.pop("latitude", None)
        lng = validated_data.pop("longitude", None)
        instance = super().create(validated_data)

        if lat is not None and lng is not None:
            instance.coordinates = Point(float(lng), float(lat), srid=4326)
            instance.save(update_fields=["coordinates"])
        return instance

    def update(self, instance, validated_data):
        """Update location and set coordinates if lat/long are provided."""
        lat = validated_data.pop("latitude", None)
        lng = validated_data.pop("longitude", None)
        instance = super().update(instance, validated_data)

        if lat is not None and lng is not None:
            instance.coordinates = Point(float(lng), float(lat), srid=4326)
            instance.save(update_fields=["coordinates"])
        return instance
