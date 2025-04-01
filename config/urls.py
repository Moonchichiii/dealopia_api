from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                  SpectacularSwaggerView)

# Updated Wagtail imports for version 6.x
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet

# Admin site configuration
admin.site.site_header = "Dealopia Administration"
admin.site.site_title = "Dealopia Admin Portal"
admin.site.index_title = "Welcome to Dealopia Admin"

# Create the API router for Wagtail
api_router = WagtailAPIRouter('wagtailapi')

# Register the API endpoints
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    
    # Wagtail CMS
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # API endpoints
    path("api/v1/", include("api.v1.urls")),
    path("api/wagtail/", api_router.urls),
    
    # Must be at the end: Wagtail catch-all
    path("", include(wagtail_urls)),
]

# Static and media files configuration
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass