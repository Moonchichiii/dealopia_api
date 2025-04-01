from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    has_2fa_enabled = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "preferred_language",
            "location",
            "favorite_categories",
            "notification_preferences",
            "has_2fa_enabled",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "date_joined",
            "last_login",
            "has_2fa_enabled",
        ]

    def get_has_2fa_enabled(self, obj):
        return (
            getattr(obj, "has_2fa_enabled", None)
            or TOTPDevice.objects.filter(user=obj, confirmed=True).exists()
        )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
            "preferred_language",
        ]

    def validate_email(self, value):
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                _(
                    "This email address is already in use. Please use a different email address or try to log in."
                )
            )
        return normalized_email

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        if "preferred_language" in validated_data:
            default_preferences = {
                "email_notifications": True,
                "deals_notifications": True,
                "language": validated_data["preferred_language"],
                "theme": "dark",
            }
            validated_data["notification_preferences"] = default_preferences

        return User.objects.create_user(**validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        required=True, style={"input_type": "password"}
    )

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Password fields didn't match.")}
            )

        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": _(
                        "New password cannot be the same as current password."
                    )
                }
            )

        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "preferred_language",
            "location",
            "favorite_categories",
            "notification_preferences",
        ]

    def validate_notification_preferences(self, value):
        if self.instance and hasattr(self.instance, "notification_preferences"):
            current_prefs = self.instance.notification_preferences or {}
            if isinstance(value, dict):
                current_prefs.update(value)
                return current_prefs
        return value


class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={"input_type": "password"})

    def validate_new_email(self, value):
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                _("This email address is already in use.")
            )
        return normalized_email

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Password is incorrect."))
        return value
