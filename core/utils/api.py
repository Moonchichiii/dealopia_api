from rest_framework import status
from rest_framework.response import Response


def api_response(data=None, message=None, errors=None, status_code=status.HTTP_200_OK):
    """
    Create a standardized API response.
    
    Args:
        data: The response data (any serializable object)
        message: A success/info message to return
        errors: Error details (string or dict for field errors)
        status_code: HTTP status code
        
    Returns:
        Response object with standardized format
    """
    is_success = status_code < 400
    
    response_body = {
        "status": "success" if is_success else "error",
    }
    
    # Include data for successful responses
    if is_success and data is not None:
        response_body["data"] = data
    
    # Include message if provided
    if message:
        if is_success:
            response_body["message"] = message
        else:
            response_body["error"] = message
    
    # Include detailed errors if provided
    if errors:
        response_body["errors"] = errors
    
    return Response(response_body, status=status_code)


def error_response(message=None, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Create a standardized error response.
    
    Args:
        message: Primary error message
        errors: Detailed error information (field-level errors)
        status_code: HTTP status code for the response
        
    Returns:
        Response object with standardized error format
    """
    return api_response(
        message=message, 
        errors=errors, 
        status_code=status_code
    )


def not_found_response(message="Resource not found"):
    """Standardized 404 Not Found response."""
    return error_response(message=message, status_code=status.HTTP_404_NOT_FOUND)


def validation_error_response(errors, message="Validation failed"):
    """Standardized validation error response."""
    return error_response(message=message, errors=errors, status_code=status.HTTP_400_BAD_REQUEST)


def permission_denied_response(message="Permission denied"):
    """Standardized permission denied response."""
    return error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)


def service_unavailable_response(message="Service temporarily unavailable"):
    """Standardized service unavailable response."""
    return error_response(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)