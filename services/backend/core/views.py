from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from core.utils.api import api_response, error_response


class BaseModelViewSet(viewsets.ModelViewSet):
    """Enhanced ModelViewSet with standardized response formatting and common filtering."""

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_serializer_context(self):
        """Add common context to serializers."""
        return super().get_serializer_context()

    def finalize_response(self, request, response, *args, **kwargs):
        """Standardize response format for all methods."""
        # Skip standardization for non-JSON responses
        if (
            hasattr(response, "accepted_renderer")
            and not getattr(response.accepted_renderer, "format", None) == "json"
        ):
            return super().finalize_response(request, response, *args, **kwargs)

        # Skip for already formatted responses
        if isinstance(response.data, dict) and "status" in response.data:
            return super().finalize_response(request, response, *args, **kwargs)

        # Skip for errors that were already formatted
        if (
            response.status_code >= 400
            and isinstance(response.data, dict)
            and "error" in response.data
        ):
            return super().finalize_response(request, response, *args, **kwargs)

        # Format successful responses
        if response.status_code < 400:
            response.data = {"status": "success", "data": response.data}
        # Format error responses
        else:
            error_msg = response.data.get("detail", "An error occurred")
            errors = None

            # Handle DRF validation errors
            if isinstance(response.data, dict) and any(
                key for key in response.data.keys() if key != "detail"
            ):
                errors = {k: v for k, v in response.data.items() if k != "detail"}

            response.data = {"status": "error", "error": error_msg}

            if errors:
                response.data["errors"] = errors

        return super().finalize_response(request, response, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """List method with standardized response."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create method with standardized response."""
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve method with standardized response."""
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update method with standardized response."""
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Destroy method with standardized response."""
        return super().destroy(request, *args, **kwargs)
