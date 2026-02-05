import logging
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DatabaseError, IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("dealopia.errors")


class ServiceError(Exception):
    """
    Base exception for service layer errors.

    Provides standardized error reporting with optional error codes
    and additional context data.
    """

    def __init__(self, message, code=None, data=None, status_code=None):
        self.message = message
        self.code = code
        self.data = data or {}
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ServiceError):
    """Resource not found error."""

    def __init__(self, message="Resource not found", **kwargs):
        kwargs.setdefault("code", "not_found")
        kwargs.setdefault("status_code", status.HTTP_404_NOT_FOUND)
        super().__init__(message, **kwargs)


class ValidationError(ServiceError):
    """Validation error for invalid input data."""

    def __init__(self, message="Invalid data", **kwargs):
        kwargs.setdefault("code", "validation_error")
        kwargs.setdefault("status_code", status.HTTP_400_BAD_REQUEST)
        super().__init__(message, **kwargs)


class PermissionError(ServiceError):
    """Permission denied error."""

    def __init__(self, message="Permission denied", **kwargs):
        kwargs.setdefault("code", "permission_denied")
        kwargs.setdefault("status_code", status.HTTP_403_FORBIDDEN)
        super().__init__(message, **kwargs)


class ServiceUnavailableError(ServiceError):
    """Service temporarily unavailable error."""

    def __init__(self, message="Service temporarily unavailable", **kwargs):
        kwargs.setdefault("code", "service_unavailable")
        kwargs.setdefault("status_code", status.HTTP_503_SERVICE_UNAVAILABLE)
        super().__init__(message, **kwargs)


def service_exception_handler(func):
    """
    Decorator to standardize error handling in service methods.

    Catches common exceptions and converts them to appropriate ServiceError types
    for standardized API responses.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ObjectDoesNotExist as e:
            logger.info(f"Not found error in {func.__name__}: {str(e)}")
            raise NotFoundError(str(e))
        except Http404 as e:
            logger.info(f"Not found error in {func.__name__}: {str(e)}")
            raise NotFoundError(str(e))
        except PermissionDenied as e:
            logger.warning(f"Permission denied in {func.__name__}: {str(e)}")
            raise PermissionError(str(e))
        except IntegrityError as e:
            logger.error(f"Integrity error in {func.__name__}: {str(e)}")
            raise ValidationError(f"Data integrity error: {str(e)}")
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise ServiceError(
                "Database error occurred",
                code="database_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ServiceError:
            # Pass through if already a ServiceError
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            raise ServiceError(
                f"Unexpected error: {str(e)}",
                code="internal_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return wrapper


def api_exception_handler(exc, context):
    """
    Custom exception handler for API views.

    Provides consistent error formatting for all API responses.
    """
    # First try the default DRF handler
    response = exception_handler(exc, context)

    # Handle ServiceError if not already handled
    if response is None and isinstance(exc, ServiceError):
        error_data = {
            "status": "error",
            "error": exc.message,
        }

        if exc.code:
            error_data["code"] = exc.code

        if exc.data:
            error_data["details"] = exc.data

        status_code = exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
        response = Response(error_data, status=status_code)

    # Standardize other DRF responses
    elif response is not None:
        # Convert to our standard format
        error_message = str(exc)
        if hasattr(exc, "detail"):
            error_message = str(exc.detail)

        error_data = {
            "status": "error",
            "error": error_message,
        }

        # Handle validation errors (with multiple fields)
        if hasattr(exc, "detail") and isinstance(exc.detail, dict):
            error_data["details"] = exc.detail

        response.data = error_data

    return response


def get_object_or_404(model_class, **kwargs):
    """
    Get an object or raise a NotFoundError.

    Similar to Django's get_object_or_404 but raises our custom NotFoundError.
    """
    try:
        return model_class.objects.get(**kwargs)
    except model_class.DoesNotExist:
        raise NotFoundError(f"{model_class.__name__} not found")
