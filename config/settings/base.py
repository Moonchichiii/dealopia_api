"""
Base settings for Dealopia API project.
Contains common settings shared across all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security settings
SECRET_KEY = config("SECRET_KEY", default="django-insecure-your-secret-key-here")
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="", cast=lambda v: [s.strip() for s in v.split(",") if s]
)
DEBUG = config("DEBUG", default=True, cast=bool)

# Application definition
INSTALLED_APPS = [
    # Django apps
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sites",
    # Third-party apps
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "wagtail",
    "corsheaders",
    "django_redis",
    "leaflet",
    "django_filters",
    "django_extensions",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_prometheus",
    # Dealopia apps
    "apps.accounts",
    "apps.deals",
    "apps.shops",
    "apps.categories",
    "apps.locations",
    "apps.scrapers",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.performance.PerformanceMiddleware",
    "core.middleware.security.SecurityMiddleware",
    "core.middleware.language.UserLanguageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

SITE_ID = 1

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "dealopia",
        "USER": "postgres",
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": "localhost",
        "PORT": "5433",
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"sslmode": "prefer"},
    }
}

# GeoDjango settings
SPATIALITE_LIBRARY_PATH = "mod_spatialite"
GDAL_LIBRARY_PATH = "C:/OSGeo4W/bin/gdal310.dll"
GEOS_LIBRARY_PATH = "C:/OSGeo4W/bin/geos_c.dll"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
    ("fr", _("French")),
    ("de", _("German")),
    ("it", _("Italian")),
    ("pt", _("Portuguese")),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static_collected")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_COOKIE": "auth-token",
    "AUTH_COOKIE_REFRESH": "refresh-token",
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "auth-token",
    "JWT_AUTH_REFRESH_COOKIE": "refresh-token",
    "JWT_AUTH_HTTPONLY": True,
    "TOKEN_MODEL": None,
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Dealopia] "
ACCOUNT_LOGIN_METHODS = {"email"}

LOGIN_URL = "/api/v1/auth/login/"
LOGIN_REDIRECT_URL = "/"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Dealopia API",
    "DESCRIPTION": "API for Dealopia deals and offers platform",
    "VERSION": "1.0.0",
}

LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (0, 0),
    "DEFAULT_ZOOM": 2,
    "MIN_ZOOM": 3,
    "MAX_ZOOM": 18,
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "update-expired-deals": {
        "task": "apps.deals.tasks.update_expired_deals",
        "schedule": timedelta(hours=1),
    },
    "warm-deal-caches": {
        "task": "apps.deals.tasks.warm_deal_caches",
        "schedule": timedelta(hours=3),
    },
    "update-deal-statistics": {
        "task": "apps.deals.tasks.update_deal_statistics",
        "schedule": timedelta(days=1),
    },
    "clean-outdated-deals": {
        "task": "apps.deals.tasks.clean_outdated_deals",
        "schedule": timedelta(weeks=2),
        "kwargs": {"days": 90},
    },
}

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@dealopia.com")
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")

UNFOLD = {
    "SITE_TITLE": "Dealopia Admin",
    "SITE_HEADER": "Dealopia",
    "SITE_URL": "/",
    "SITE_ICON": None,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Users",
                "icon": "person",
                "models": [
                    "accounts.user",
                ],
                "items": [],
            },
            {
                "title": "Deals",
                "icon": "shopping_bag",
                "models": [
                    "deals.deal",
                ],
                "items": [],
            },
            {
                "title": "Shops",
                "icon": "store",
                "models": [
                    "shops.shop",
                ],
                "items": [],
            },
            {
                "title": "Categories",
                "icon": "category",
                "models": [
                    "categories.category",
                ],
                "items": [],
            },
            {
                "title": "Locations",
                "icon": "location_on",
                "models": [
                    "locations.location",
                ],
                "items": [],
            },
        ],
    },
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
    "ENVIRONMENT": "development",
    "ENVIRONMENT_COLOR": "#FFC107",
}

LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)s",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "dealopia.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "error.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "json",
        },
        "performance_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "performance.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "security.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
            "formatter": "verbose",
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "django.server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "security_file", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "dealopia": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "dealopia.performance": {
            "handlers": ["console", "performance_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "dealopia.errors": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "dealopia.scrapers": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "dealopia.api_integration": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "dealopia.security": {
            "handlers": ["console", "security_file", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

SLOW_REQUEST_THRESHOLD = 1.0


SPECTACULAR_SETTINGS = {
    "TITLE": "Dealopia API",
    "DESCRIPTION": "API for sustainable deals marketplace",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Deals", "description": "Manage eco-friendly deals"},
        {"name": "Shops", "description": "Manage sustainable shops"},
        {"name": "Categories", "description": "Organize deals and shops"},
        {"name": "Locations", "description": "Geospatial functionality"},
    ],
}
