from django.db import models
from django.contrib.auth.models import AbstractUser

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
]

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, null=True, blank=True)
    favorite_categories = models.ManyToManyField('categories.Category', blank=True)
    notification_preferences = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return self.username
