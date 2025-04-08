import json

from django.utils import timezone
from rest_framework import serializers
from cloudinary.utils import cloudinary_url

from api.v1.serializers.categories import CategoryListSerializer
from apps.shops.models import Shop


class ShopListSerializer(serializers.ModelSerializer):
    category_names = serializers.StringRelatedField(
        source="categories", many=True, read_only=True
    )
    deal_count = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "logo",
            "logo_url",
            "short_description",
            "category_names",
            "is_verified",
            "is_featured",
            "rating",
            "deal_count",
            "distance",
            "banner_url",
        ]
        read_only_fields = ["id", "is_verified", "rating", "distance"]

    def get_deal_count(self, obj):
        now = timezone.now()
        if hasattr(obj, "prefetched_deals"):
            return sum(
                1
                for deal in obj.prefetched_deals
                if deal.is_verified and deal.start_date <= now and deal.end_date >= now
            )
        return obj.deals.filter(
            is_verified=True,
            start_date__lte=now,
            end_date__gte=now,
        ).count()

    def get_distance(self, obj):
        if hasattr(obj, "distance") and obj.distance:
            return round(obj.distance.km, 1)
        return None

    def get_logo_url(self, obj):
        """
        Generate optimized Cloudinary URL for the shop logo.
        
        Returns a properly formatted Cloudinary URL with transformations
        if the shop has a logo image, or None otherwise.
        """
        if not obj.logo:
            return None
            
        if hasattr(obj.logo, 'file') and hasattr(obj.logo.file, 'public_id'):
            # This is a Cloudinary image, generate optimized URL
            options = {
                "quality": "auto",
                "fetch_format": "auto",
                "width": 300,  # Appropriate size for logos
                "crop": "fit",
            }
            url, _ = cloudinary_url(obj.logo.file.public_id, **options)
            return url
        
        # Fallback for non-Cloudinary images
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return obj.logo.url
        
    def get_banner_url(self, obj):
        """
        Generate optimized Cloudinary URL for the shop banner.
        
        Returns a properly formatted Cloudinary URL with transformations
        if the shop has a banner image, or None otherwise.
        """
        if not hasattr(obj, 'banner_image') or not obj.banner_image:
            return None
            
        if hasattr(obj.banner_image, 'file') and hasattr(obj.banner_image.file, 'public_id'):
            # This is a Cloudinary image, generate optimized URL
            options = {
                "quality": "auto",
                "fetch_format": "auto",
                "width": 1200,  # Banner width
                "height": 400,  # Banner height
                "crop": "fill",
                "gravity": "auto",
            }
            url, _ = cloudinary_url(obj.banner_image.file.public_id, **options)
            return url
        
        # Fallback for non-Cloudinary images
        request = self.context.get("request")
        if request and obj.banner_image:
            return request.build_absolute_uri(obj.banner_image.url)
        return obj.banner_image.url if obj.banner_image else None


class ShopSerializer(ShopListSerializer):
    categories = CategoryListSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    active_deals = serializers.SerializerMethodField()
    location_details = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ShopListSerializer.Meta.fields + [
            "description",
            "banner_image",
            "website",
            "phone",
            "email",
            "categories",
            "location",
            "location_details",
            "opening_hours",
            "owner",
            "owner_name",
            "active_deals",
            "created_at",
            "updated_at",
            "sustainability_score",
            "carbon_neutral",
            "sustainability_initiatives",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "rating",
            "created_at",
            "updated_at",
            "owner_name",
        ]

    def get_owner_name(self, obj):
        if not obj.owner:
            return None
        return obj.owner.get_full_name() or obj.owner.email

    def get_active_deals(self, obj):
        from api.v1.serializers.deals import DealListSerializer

        deals = obj.deals.filter(
            is_verified=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        ).order_by("-is_featured", "-created_at")[:5]
        return DealListSerializer(deals, many=True, context=self.context).data

    def get_location_details(self, obj):
        if not obj.location:
            return None
        return {
            "address": obj.location.address,
            "city": obj.location.city,
            "state": obj.location.state,
            "country": obj.location.country,
            "postal_code": obj.location.postal_code,
            "latitude": (
                obj.location.coordinates.y if obj.location.coordinates else None
            ),
            "longitude": (
                obj.location.coordinates.x if obj.location.coordinates else None
            ),
        }

    def validate(self, data):
        if "opening_hours" in data:
            if not isinstance(data["opening_hours"], dict):
                raise serializers.ValidationError(
                    {"opening_hours": "Opening hours must be a JSON object"}
                )
            for day, hours in data["opening_hours"].items():
                if not isinstance(hours, str):
                    raise serializers.ValidationError(
                        {"opening_hours": f"Hours for {day} must be a string"}
                    )
        return data


class ShopCreateSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False, allow_null=True)
    banner_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "description",
            "short_description",
            "logo",
            "banner_image",
            "website",
            "phone",
            "email",
            "categories",
            "location",
            "opening_hours",
            "sustainability_initiatives",
            "carbon_neutral",
        ]

    def validate_opening_hours(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON for opening_hours.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data.update({
            "owner": user, 
            "is_verified": False, 
            "rating": 0,
            "sustainability_score": 5.0,
        })
        return super().create(validated_data)