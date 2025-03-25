from .base import *

import os
import dj_database_url
from decouple import config

# Core Django Settings
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='dealopia.com,www.dealopia.com,api.dealopia.com',
    cast=lambda v: [s.strip() for s in v.split(',') if s]
)

# Security Settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# Database Configuration
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config('REDIS_URL', default='redis://localhost:6379/1'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Static Files Configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media Files Configuration
INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default='')
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# Admin Interface Configuration
if 'UNFOLD' in locals():
    UNFOLD['ENVIRONMENT'] = 'production'
    UNFOLD['ENVIRONMENT_COLOR'] = '#4CAF50'