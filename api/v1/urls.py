from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from backend.api.v1.views.accounts import UserViewSet
from backend.api.v1.views.deals import DealViewSet
from backend.api.v1.views.shops import ShopViewSet
from backend.api.v1.views.categories import CategoryViewSet
from backend.api.v1.views.locations import LocationViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('deals', DealViewSet)
router.register('shops', ShopViewSet)
router.register('categories', CategoryViewSet)
router.register('locations', LocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', UserViewSet.as_view({'get': 'me'}), name='auth_me'),
    
    # Additional custom endpoints can be added here
    path('deals/nearby/', DealViewSet.as_view({'get': 'nearby'}), name='deals-nearby'),
    path('deals/featured/', DealViewSet.as_view({'get': 'featured'}), name='deals-featured'),
    path('deals/ending-soon/', DealViewSet.as_view({'get': 'ending_soon'}), name='deals-ending-soon'),
    
    path('shops/featured/', ShopViewSet.as_view({'get': 'featured'}), name='shops-featured'),
    
    path('locations/nearby/', LocationViewSet.as_view({'get': 'nearby'}), name='locations-nearby'),
]
