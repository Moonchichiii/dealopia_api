import re
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    """Validate that the phone number follows E.164 format"""
    if not re.match(r'^\+?[1-9]\d{1,14}$', value):
        raise ValidationError(
            _('Phone number must be in E.164 format: +[country code][number]'),
        )


def validate_discount_percentage(value):
    """Validate discount percentage is between 0 and 100"""
    if value < 0 or value > 100:
        raise ValidationError(
            _('Discount percentage must be between 0 and 100'),
        )


def validate_coupon_code(value):
    """Validate coupon codes follow pattern (letters and digits only)"""
    if value and not re.match(r'^[A-Z0-9]+$', value):
        raise ValidationError(
            _('Coupon code can only contain uppercase letters and numbers'),
        )


def validate_future_date(value):
    """Validate that a date is in the future"""
    if value < timezone.now():
        raise ValidationError(
            _('Date must be in the future'),
        )
