from .base import *
import dj_database_url
from decouple import config

# Core Settings
DEBUG = config('STAGING_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config(
    'STAGING_ALLOWED_HOSTS',
    default='staging.dealopia.com,staging-api.dealopia.com',
    cast=lambda v: [s.strip() for s in v.split(',') if s]
)

# Security Settings
SECURE_SSL_REDIRECT = config('STAGING_SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('STAGING_SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('STAGING_CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('STAGING_SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('STAGING_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('STAGING_SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database Settings
DATABASE_URL = config('STAGING_DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'dealopia_staging',
            'USER': config('STAGING_DB_USER', default='postgres'),
            'PASSWORD': config('STAGING_DB_PASSWORD'),
            'HOST': config('STAGING_DB_HOST', default='localhost'),
            'PORT': config('STAGING_DB_PORT', default='5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {'sslmode': 'prefer'},
        }
    }

# Cache Settings
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config('STAGING_REDIS_URL', default='redis://localhost:6379/2'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "MAX_ENTRIES": 5000,
        }
    }
}

# Media Storage
INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('STAGING_CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('STAGING_CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('STAGING_CLOUDINARY_API_SECRET', default='')
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Email Settings
EMAIL_BACKEND = config('STAGING_EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('STAGING_EMAIL_HOST', default='')
EMAIL_PORT = config('STAGING_EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('STAGING_EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('STAGING_EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('STAGING_EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_SUBJECT_PREFIX = '[Dealopia Staging] '

# Development Tools
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1']
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: True}

# Performance Settings
CELERY_WORKER_CONCURRENCY = 2
TRACK_PERFORMANCE_IN_DEBUG = True

# Environment Indicator
UNFOLD['ENVIRONMENT'] = 'staging'
UNFOLD['ENVIRONMENT_COLOR'] = '#FF9800'  # Orange for staging
