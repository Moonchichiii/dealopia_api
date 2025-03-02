from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from api.v1.views.accounts import UserViewSet
from api.v1.views.deals import DealViewSet
from api.v1.views.shops import ShopViewSet
from api.v1.views.categories import CategoryViewSet
from api.v1.views.locations import LocationViewSet
from api.v1.views.auth import TwoFactorVerifyView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'deals', DealViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'locations', LocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints (dj-rest-auth)
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Email confirmation endpoint
    re_path(
    r"^auth/registration/account-confirm-email/(?P<key>[-:\w]+)/",
    include("allauth.urls"),
    name="account_confirm_email",
),
    
    # JWT token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Social auth endpoints
    path('auth/google/', include('allauth.socialaccount.providers.google.urls')),
    
    # User profile endpoint
    path('auth/me/', UserViewSet.as_view({'get': 'me'}), name='auth_me'),
    
    # Custom deal endpoints
    path('deals/nearby/', DealViewSet.as_view({'get': 'nearby'}), name='deals-nearby'),
    path('deals/featured/', DealViewSet.as_view({'get': 'featured'}), name='deals-featured'),
    path('deals/ending-soon/', DealViewSet.as_view({'get': 'ending_soon'}), name='deals-ending-soon'),
    
    # Custom shop endpoints
    path('shops/featured/', ShopViewSet.as_view({'get': 'featured'}), name='shops-featured'),
    
    # Custom location endpoints
    path('locations/nearby/', LocationViewSet.as_view({'get': 'nearby'}), name='locations-nearby'),
]

# 2FA verification endpoint
urlpatterns += [
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
]
