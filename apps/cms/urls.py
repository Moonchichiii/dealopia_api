from django.urls import include, path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from apps.cms.api import api_router, ShopWagtailViewSet, ProductWagtailViewSet

app_name = "cms"

urlpatterns = [
    # Wagtail admin
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    
    # Wagtail API 
    path("cms/api/", api_router.urls),
    
    # Preview endpoints
    path("shop-cms-preview/<int:pk>/", 
         ShopWagtailViewSet.as_view({"get": "cms_preview"}), 
         name="shop-cms-preview"),
    path("product-cms-preview/<int:pk>/", 
         ProductWagtailViewSet.as_view({"get": "cms_preview"}), 
         name="product-cms-preview"),
]
