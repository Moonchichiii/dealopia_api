"""
Base settings for Dealopia API project.
Contains common settings shared across all environments.
"""
import os
from pathlib import Path
from datetime import timedelta
from decouple import config
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='', 
    cast=lambda v: [s.strip() for s in v.split(',') if s]
)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
# Application definition
INSTALLED_APPS = [
    # Django apps
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',  # Add this line
    'rest_framework_simplejwt',
    'drf_spectacular',
    'wagtail',
    'corsheaders',
    'django_redis',
    'leaflet',
    'django_filters',
    'django_extensions',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_prometheus',
    
    # Dealopia apps
    'apps.accounts',
    'apps.deals',
    'apps.shops',
    'apps.categories',
    'apps.locations',
    'apps.scrapers',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.performance.PerformanceMiddleware',
    'core.middleware.security.SecurityMiddleware',
    'core.middleware.language.UserLanguageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Site ID is required for django-allauth
SITE_ID = 1

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configurations remain the same
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'dealopia',
        'USER': 'postgres',
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

# GeoDjango settings
SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
GDAL_LIBRARY_PATH = 'C:/OSGeo4W/bin/gdal310.dll'
GEOS_LIBRARY_PATH = 'C:/OSGeo4W/bin/geos_c.dll'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization settings remain the same
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian')),
    ('pt', _('Portuguese')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files and Media settings remain the same
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

# dj-rest-auth settings
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'auth-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,
    'TOKEN_MODEL': None,
}

# django-allauth settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Dealopia] '
LOGIN_URL = '/api/v1/auth/login/'
LOGIN_REDIRECT_URL = '/'

# Social account settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Dealopia API',
    'DESCRIPTION': 'API for Dealopia deals and offers platform',
    'VERSION': '1.0.0',
}

# Other settings remain the same
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (0, 0),
    'DEFAULT_ZOOM': 2,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
}

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE


# Unfold Admin settings remain the same
UNFOLD = {
    "SITE_TITLE": "Dealopia Admin",
    "SITE_HEADER": "Dealopia",
    "SITE_URL": "/",
    "SITE_ICON": None,
    
    # Sidebar menu customization
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Users",
                "icon": "person",
                "models": [
                    "accounts.user",
                ]
            },
            {
                "title": "Deals",
                "icon": "shopping_bag",
                "models": [
                    "deals.deal",
                ]
            },
            {
                "title": "Shops",
                "icon": "store",
                "models": [
                    "shops.shop",
                ]
            },
            {
                "title": "Categories",
                "icon": "category",
                "models": [
                    "categories.category",
                ]
            },
            {
                "title": "Locations",
                "icon": "location_on",
                "models": [
                    "locations.location",
                ]
            },
        ]
    },
    
    # Theme configuration
    "COLORS": {
        "primary": {
            "50": "240 249 255",
            "100": "224 242 254",
            "200": "186 230 253",
            "300": "125 211 252",
            "400": "56 189 248",
            "800": "7 89 133",
            "900": "12 74 110",
            "950": "8 47 73",
        },
    },
    
    # Environment indicator
    "ENVIRONMENT": "development",
    "ENVIRONMENT_COLOR": "#FFC107",
}