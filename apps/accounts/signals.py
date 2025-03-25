# apps/accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.accounts.models import User


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """Signal handler for User post_save"""
    if created:
        # Initialize user preferences and settings for new users
        if not instance.notification_preferences:
            instance.notification_preferences = {
                'email_notifications': True,
                'deals_notifications': True,
                'language': instance.preferred_language or 'en',
                'theme': 'dark'  # Default theme
            }
            
            # Save without triggering the signal again
            User.objects.filter(pk=instance.pk).update(
                notification_preferences=instance.notification_preferences
            )
            
        # Additional initialization logic can be added here
        # For example, creating a welcome notification


@receiver(pre_save, sender=User)
def handle_user_pre_save(sender, instance, **kwargs):
    """Signal handler for User pre_save"""
    if instance.pk:
        # Get the old instance from database
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Check if password has changed
            if instance.password != old_instance.password:
                # Flag for password change to be used in post_save
                instance._password_changed = True
                
            # Check if account is being deactivated
            if old_instance.is_active and not instance.is_active:
                # Flag for deactivation to be used in post_save
                instance._being_deactivated = True
                
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def handle_password_change(sender, instance, **kwargs):
    """Handle password change by invalidating all tokens"""
    if hasattr(instance, '_password_changed') and instance._password_changed:
        # Blacklist all outstanding tokens for the user
        tokens = OutstandingToken.objects.filter(user_id=instance.id)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
            
        # Remove the flag
        delattr(instance, '_password_changed')
        
        # Log the password change event
        from datetime import datetime
        instance.notification_preferences = instance.notification_preferences or {}
        security_events = instance.notification_preferences.get('security_events', [])
        security_events.append({
            'event': 'password_changed',
            'timestamp': datetime.now().isoformat(),
            'ip_address': getattr(instance, '_request_ip', None)
        })
        instance.notification_preferences['security_events'] = security_events
        User.objects.filter(pk=instance.pk).update(
            notification_preferences=instance.notification_preferences
        )


@receiver(post_save, sender=User)
def handle_account_deactivation(sender, instance, **kwargs):
    """Handle account deactivation by invalidating all tokens"""
    if hasattr(instance, '_being_deactivated') and instance._being_deactivated:
        # Blacklist all outstanding tokens for the user
        tokens = OutstandingToken.objects.filter(user_id=instance.id)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
            
        # Remove the flag
        delattr(instance, '_being_deactivated')
        
        # Log the deactivation event
        from datetime import datetime
        instance.notification_preferences = instance.notification_preferences or {}
        security_events = instance.notification_preferences.get('security_events', [])
        security_events.append({
            'event': 'account_deactivated',
            'timestamp': datetime.now().isoformat(),
            'ip_address': getattr(instance, '_request_ip', None)
        })
        instance.notification_preferences['security_events'] = security_events
        User.objects.filter(pk=instance.pk).update(
            notification_preferences=instance.notification_preferences
        )


@receiver(user_logged_in)
def update_last_login(sender, user, request, **kwargs):
    """Update last login time and track login events"""
    # Update last login time
    user.last_login = timezone.now()
    
    # Track login for security purposes
    from datetime import datetime
    user.notification_preferences = user.notification_preferences or {}
    
    # Store IP address for the request context in the User view
    if request:
        user._request_ip = request.META.get('REMOTE_ADDR')
    
    # Track login events
    login_events = user.notification_preferences.get('login_events', [])
    login_events.append({
        'timestamp': datetime.now().isoformat(),
        'ip_address': getattr(user, '_request_ip', None),
        'user_agent': request.META.get('HTTP_USER_AGENT') if request else None
    })
    
    # Keep only last 10 login events
    user.notification_preferences['login_events'] = login_events[-10:]
    
    # Save without triggering other signals
    User.objects.filter(pk=user.pk).update(
        last_login=user.last_login,
        notification_preferences=user.notification_preferences
    )