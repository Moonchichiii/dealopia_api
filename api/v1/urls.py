# api/v1/urls.py - Enhanced URL configuration
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView

# Import views
from api.v1.views.accounts import UserViewSet
from api.v1.views.deals import DealViewSet
from api.v1.views.shops import ShopViewSet
from api.v1.views.categories import CategoryViewSet
from api.v1.views.locations import LocationViewSet
from api.v1.views.auth import (
    CustomTokenObtainPairView,
    TwoFactorVerifyView,
    TwoFactorSetupView,
    TwoFactorDisableView,
    SocialAuthCallbackView,
    SessionInfoView,
    TokenRefreshRateLimitedView
)

# Setup router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'deals', DealViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'locations', LocationViewSet)

# Authentication URLs with enhanced flexibility
auth_patterns = [
    # Standard auth endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', include('dj_rest_auth.urls')),
    
    # Registration endpoints
    path('registration/', include('dj_rest_auth.registration.urls')),
    
    # Email confirmation and verification
    re_path(
        r"^registration/account-confirm-email/(?P<key>[-:\w]+)/",
        include("allauth.urls"),
        name="account_confirm_email",
    ),
    path('registration/verify-email/', include('dj_rest_auth.registration.urls')),
    path('registration/resend-email/', include('dj_rest_auth.registration.urls')),
    
    # Password management
    path('password/reset/', include('dj_rest_auth.urls')),
    path('password/reset/confirm/', include('dj_rest_auth.urls')),
    path('password/change/', include('dj_rest_auth.urls')),
    
    # JWT token endpoints
    path('token/refresh/', TokenRefreshRateLimitedView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Social auth endpoints
    path('google/', include('allauth.socialaccount.providers.google.urls')),
    path('facebook/', include('allauth.socialaccount.providers.facebook.urls')),
    path('github/', include('allauth.socialaccount.providers.github.urls')),
    path('social-callback/', SocialAuthCallbackView.as_view(), name='social_callback'),
    
    # Two-factor authentication
    path('2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa_disable'),
    
    # Session info and user profile
    path('me/', UserViewSet.as_view({'get': 'me'}), name='auth_me'),
    path('session-info/', SessionInfoView.as_view(), name='session_info'),
]

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Auth endpoints under /auth/
    path('auth/', include(auth_patterns)),
    
    # Custom deal endpoints
    path('deals/nearby/', DealViewSet.as_view({'get': 'nearby'}), name='deals-nearby'),
    path('deals/featured/', DealViewSet.as_view({'get': 'featured'}), name='deals-featured'),
    path('deals/ending-soon/', DealViewSet.as_view({'get': 'ending_soon'}), name='deals-ending-soon'),
    
    # Custom shop endpoints
    path('shops/featured/', ShopViewSet.as_view({'get': 'featured'}), name='shops-featured'),
    
    # Custom location endpoints
    path('locations/nearby/', LocationViewSet.as_view({'get': 'nearby'}), name='locations-nearby'),
]