from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """User serializer with 2FA status."""
    
    has_2fa_enabled = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone_number', 'avatar', 'preferred_language',
            'location', 'favorite_categories', 'notification_preferences',
            'has_2fa_enabled', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login', 'has_2fa_enabled']
    
    def get_has_2fa_enabled(self, obj):
        """Check if user has 2FA enabled."""
        # Use getattr to gracefully handle the case when using a prefetched instance
        return getattr(obj, 'has_2fa_enabled', None) or TOTPDevice.objects.filter(user=obj, confirmed=True).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """User registration serializer with validation."""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number',
            'preferred_language'
        ]
    
    def validate_email(self, value):
        """Validate that email is not already in use."""
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                _("This email address is already in use. Please use a different email address or try to log in.")
            )
        return normalized_email
    
    def validate_password(self, value):
        """Validate password meets complexity requirements."""
        validate_password(value)
        return value
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        return attrs
    
    def create(self, validated_data):
        """Create a new user with validated data."""
        # Remove password confirmation as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Set default notification preferences if language specified
        if 'preferred_language' in validated_data:
            default_preferences = {
                'email_notifications': True,
                'deals_notifications': True,
                'language': validated_data['preferred_language'],
                'theme': 'dark'
            }
            validated_data['notification_preferences'] = default_preferences
        
        # Use User.objects.create_user to properly hash the password
        return User.objects.create_user(**validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """Password change with current password verification."""
    
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_current_password(self, value):
        """Verify current password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value
    
    def validate_new_password(self, value):
        """Validate new password meets complexity requirements."""
        validate_password(value, self.context['request'].user)
        return value
    
    def validate(self, attrs):
        """Validate passwords match and aren't the same as current password."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": _("Password fields didn't match.")})
            
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": _("New password cannot be the same as current password.")})
        
        return attrs
    
    def save(self):
        """Save the new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """User profile update serializer."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'avatar', 'preferred_language', 'location',
            'favorite_categories', 'notification_preferences'
        ]
    
    def validate_notification_preferences(self, value):
        """Merge notification preferences with existing ones."""
        if self.instance and hasattr(self.instance, 'notification_preferences'):
            current_prefs = self.instance.notification_preferences or {}
            if isinstance(value, dict):
                current_prefs.update(value)
                return current_prefs
        return value


class EmailChangeRequestSerializer(serializers.Serializer):
    """Email change request serializer."""
    
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_new_email(self, value):
        """Validate email doesn't already exist."""
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(_("This email address is already in use."))
        return normalized_email
    
    def validate_password(self, value):
        """Validate password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Password is incorrect."))
        return value