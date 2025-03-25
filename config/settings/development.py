from .base import *  # noqa: F403

# Core settings
DEBUG = True

# Debug toolbar configuration
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']

# Authentication settings
REST_AUTH['JWT_AUTH_COOKIE_DOMAIN'] = 'localhost'  # noqa: F405

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]
