import decimal
from datetime import timedelta

from cloudinary.forms import CloudinaryFileField
from django.utils import timezone
from rest_framework import serializers

from api.v1.serializers.categories import CategoryListSerializer
from api.v1.serializers.shops import ShopListSerializer
from apps.deals.models import Deal


class DealListSerializer(serializers.ModelSerializer):
    shop_name = serializers.ReadOnlyField(source="shop.name")
    shop_logo = serializers.SerializerMethodField()
    category_names = serializers.StringRelatedField(
        source="categories", many=True, read_only=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    time_left = serializers.SerializerMethodField()
    is_eco_friendly = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            "id",
            "title",
            "shop",
            "shop_name",
            "shop_logo",
            "original_price",
            "discounted_price",
            "discount_percentage",
            "discount_amount",
            "categories",
            "category_names",
            "image",
            "start_date",
            "end_date",
            "is_featured",
            "is_exclusive",
            "is_verified",
            "time_left",
            "is_eco_friendly",
            "sustainability_score",
            "local_production",
            "coupon_code",
            "distance",
        ]
        read_only_fields = [
            "id",
            "discount_amount",
            "time_left",
            "is_eco_friendly",
            "distance",
        ]

    def get_shop_logo(self, obj):
        return obj.shop.logo.url if obj.shop.logo else None

    def get_time_left(self, obj):
        now = timezone.now()
        if now > obj.end_date:
            return "Expired"
        delta = obj.end_date - now
        if delta.days > 0:
            return f"{delta.days} days"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} hours"
        minutes = (delta.seconds % 3600) // 60
        return f"{minutes} minutes"

    def get_is_eco_friendly(self, obj):
        return obj.sustainability_score >= 6.0

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            return round(obj.distance.km, 1)
        return None


class DealSerializer(DealListSerializer):
    image = CloudinaryFileField(
        options={
            "folder": "deals",
            "resource_type": "image",
            "transformation": {"quality": "auto:good", "fetch_format": "auto"},
        },
        required=False,
    )

    def validate(self, data):
        if "original_price" in data and "discounted_price" in data:
            if data["discounted_price"] >= data["original_price"]:
                raise serializers.ValidationError(
                    "Discounted price must be lower than the original price"
                )
        if "start_date" in data and "end_date" in data:
            if data["start_date"] >= data["end_date"]:
                raise serializers.ValidationError("End date must be after start date")
            if data["end_date"] < timezone.now():
                raise serializers.ValidationError("End date cannot be in the past")
        if (
            "original_price" in data
            and "discounted_price" in data
            and "discount_percentage" not in data
        ):
            try:
                discount = (
                    (data["original_price"] - data["discounted_price"])
                    / data["original_price"]
                ) * 100
                data["discount_percentage"] = round(discount)
            except (ZeroDivisionError, decimal.InvalidOperation):
                raise serializers.ValidationError(
                    "Invalid price values for discount calculation"
                )
        return data


class DealDetailSerializer(DealSerializer):
    shop = ShopListSerializer(read_only=True)
    categories = CategoryListSerializer(many=True, read_only=True)
    similar_deals = serializers.SerializerMethodField()
    eco_certifications = serializers.JSONField(required=False)

    class Meta(DealSerializer.Meta):
        fields = DealSerializer.Meta.fields + [
            "description",
            "terms_and_conditions",
            "redemption_link",
            "views_count",
            "clicks_count",
            "created_at",
            "updated_at",
            "similar_deals",
            "eco_certifications",
            "carbon_footprint",
            "source",
        ]

    def get_similar_deals(self, obj):
        from apps.deals.services import DealService

        similar = DealService.get_related_deals(obj, limit=3)
        return DealListSerializer(similar, many=True, context=self.context).data
