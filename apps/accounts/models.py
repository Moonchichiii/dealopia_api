from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import secrets


LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
]


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""
    
    use_in_migrations = True
    
    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    phone_number = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, null=True, blank=True)
    favorite_categories = models.ManyToManyField('categories.Category', blank=True)
    notification_preferences = models.JSONField(default=dict)
    sustainability_preference = models.IntegerField(default=5)
    
    # Email change management fields
    email_change_token = models.CharField(max_length=64, blank=True, null=True)
    new_email = models.EmailField(blank=True, null=True)
    email_token_created_at = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def create_email_change_request(self, new_email):
        """Generate token and store pending email change request."""
        token = secrets.token_urlsafe(43)
        
        self.email_change_token = token
        self.new_email = new_email
        self.email_token_created_at = timezone.now()
        self.save(update_fields=['email_change_token', 'new_email', 'email_token_created_at'])
        
        verification_url = f"{settings.FRONTEND_URL}/email-verification?token={token}"
        
        subject = "[Dealopia] Verify your new email address"
        message = f"""
Hello {self.get_full_name() or self.email},

We received a request to change your email address on Dealopia from {self.email} to {new_email}.

To complete this change, please verify your new email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't request this change, please ignore this email or contact our support team.

Best regards,
The Dealopia Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            fail_silently=False,
        )
        
        return token
    
    def confirm_email_change(self, token):
        """Confirm and process email change with token."""
        if not self.email_change_token or self.email_change_token != token:
            raise ValueError(_("Invalid verification token"))
        
        if not self.new_email:
            raise ValueError(_("No pending email change found"))
        
        if not self.email_token_created_at or \
           (timezone.now() - self.email_token_created_at).total_seconds() > 86400:
            raise ValueError(_("Verification token has expired"))
        
        old_email = self.email
        self.email = self.new_email
        
        self.new_email = None
        self.email_change_token = None
        self.email_token_created_at = None
        
        self.save(update_fields=['email', 'new_email', 'email_change_token', 'email_token_created_at'])
        
        subject = "[Dealopia] Your email address has been changed"
        message = f"""
Hello {self.get_full_name() or old_email},

This is to inform you that the email address associated with your Dealopia account has been changed from {old_email} to {self.email}.

If you made this change, no further action is required.

If you did not authorize this change, please contact our support team immediately.

Best regards,
The Dealopia Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[old_email],
            fail_silently=False,
        )
        
        return True
