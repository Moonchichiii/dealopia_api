from datetime import datetime

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)

from apps.accounts.models import User


def _blacklist_all_user_tokens(user_id):
    """Invalidate all tokens for security-sensitive operations"""
    tokens = OutstandingToken.objects.filter(user_id=user_id)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


def _add_security_event(instance, event_name):
    """Record security events in user preferences"""
    instance.notification_preferences = instance.notification_preferences or {}
    security_events = instance.notification_preferences.get("security_events", [])
    security_events.append(
        {
            "event": event_name,
            "timestamp": datetime.now().isoformat(),
            "ip_address": getattr(instance, "_request_ip", None),
        }
    )
    instance.notification_preferences["security_events"] = security_events
    User.objects.filter(pk=instance.pk).update(
        notification_preferences=instance.notification_preferences
    )


def _update_user_preferences(instance, updates):
    """Update user preferences without triggering signals"""
    instance.notification_preferences = instance.notification_preferences or {}
    instance.notification_preferences.update(updates)
    User.objects.filter(pk=instance.pk).update(
        notification_preferences=instance.notification_preferences
    )


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    if created and not instance.notification_preferences:
        default_prefs = {
            "email_notifications": True,
            "deals_notifications": True,
            "language": instance.preferred_language or "en",
            "theme": "dark",
        }
        _update_user_preferences(instance, default_prefs)


@receiver(pre_save, sender=User)
def handle_user_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = User.objects.get(pk=instance.pk)

        if instance.password != old_instance.password:
            instance._password_changed = True

        if old_instance.is_active and not instance.is_active:
            instance._being_deactivated = True

    except User.DoesNotExist:
        pass


@receiver(post_save, sender=User)
def handle_password_change(sender, instance, **kwargs):
    if not hasattr(instance, "_password_changed") or not instance._password_changed:
        return

    _blacklist_all_user_tokens(instance.id)
    _add_security_event(instance, "password_changed")
    delattr(instance, "_password_changed")


@receiver(post_save, sender=User)
def handle_account_deactivation(sender, instance, **kwargs):
    if not hasattr(instance, "_being_deactivated") or not instance._being_deactivated:
        return

    _blacklist_all_user_tokens(instance.id)
    _add_security_event(instance, "account_deactivated")
    delattr(instance, "_being_deactivated")


@receiver(user_logged_in)
def update_last_login(sender, user, request, **kwargs):
    user.last_login = timezone.now()

    if request:
        user._request_ip = request.META.get("REMOTE_ADDR")

    login_events = user.notification_preferences.get("login_events", [])
    login_events.append(
        {
            "timestamp": datetime.now().isoformat(),
            "ip_address": getattr(user, "_request_ip", None),
            "user_agent": request.META.get("HTTP_USER_AGENT") if request else None,
        }
    )

    updates = {"login_events": login_events[-10:]}
    _update_user_preferences(user, updates)

    # Update last_login separately
    User.objects.filter(pk=user.pk).update(last_login=user.last_login)
