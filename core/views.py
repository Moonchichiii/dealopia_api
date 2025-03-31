from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from core.utils.api import api_response, error_response


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Enhanced ModelViewSet with standardized responses and common functionality.

    Features:
    - Standardized response formatting
    - Common filter backends
    - Custom response methods
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_serializer_context(self):
        """Add common context to serializers."""
        context = super().get_serializer_context()
        # Add additional common context here if needed
        return context

    def finalize_response(self, request, response, *args, **kwargs):
        """Standardize response format for all methods."""
        # Skip standardization for non-JSON responses (like BrowsableAPIRenderer)
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
        """Enhanced list method with standardized response."""
        response = super().list(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        """Enhanced create method with standardized response."""
        response = super().create(request, *args, **kwargs)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Enhanced retrieve method with standardized response."""
        response = super().retrieve(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        """Enhanced update method with standardized response."""
        response = super().update(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        """Enhanced destroy method with standardized response."""
        response = super().destroy(request, *args, **kwargs)
        return response
