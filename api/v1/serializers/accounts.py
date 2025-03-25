# api/v1/serializers/accounts.py
from rest_framework import serializers
from apps.accounts.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice


class UserSerializer(serializers.ModelSerializer):
    """Enhanced user serializer with additional fields and validations"""
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
        """Check if user has 2FA enabled"""
        return TOTPDevice.objects.filter(user=obj, confirmed=True).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for user registration with strong validation"""
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
        """Validate email is unique with better error messages"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("This email address is already in use. Please use a different email address or try to log in.")
            )
        return value.lower()  # Normalize to lowercase
    
    def validate_password(self, value):
        """Validate password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Password fields didn't match.")})
        return attrs
    
    def create(self, validated_data):
        """Create user with encrypted password and remove password_confirm"""
        validated_data.pop('password_confirm')
        
        # You may perform additional operations before creating the user
        # Such as setting default preferences based on user language
        if 'preferred_language' in validated_data:
            default_preferences = {
                'email_notifications': True,
                'deals_notifications': True,
                'language': validated_data['preferred_language'],
                'theme': 'dark'  # Default theme
            }
            validated_data['notification_preferences'] = default_preferences
        
        user = User.objects.create_user(**validated_data)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change with current password verification"""
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value
    
    def validate_new_password(self, value):
        try:
            validate_password(value, self.context['request'].user)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": _("Password fields didn't match.")})
            
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": _("New password cannot be the same as current password.")})
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile without changing email/password"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'avatar', 'preferred_language', 'location',
            'favorite_categories', 'notification_preferences'
        ]
    
    def validate_notification_preferences(self, value):
        """Ensure notification preferences don't lose existing values"""
        if self.instance and hasattr(self.instance, 'notification_preferences'):
            current_prefs = self.instance.notification_preferences or {}
            # Update rather than replace
            if isinstance(value, dict):
                for key, val in value.items():
                    current_prefs[key] = val
                return current_prefs
        return value


class EmailChangeRequestSerializer(serializers.Serializer):
    """Serializer for email change request"""
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_new_email(self, value):
        """Validate new email is unique"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("This email address is already in use."))
        return value.lower()
    
    def validate_password(self, value):
        """Validate user password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Password is incorrect."))
        return value