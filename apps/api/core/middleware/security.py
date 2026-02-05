from django.utils.deprecation import MiddlewareMixin


class SecurityMiddleware(MiddlewareMixin):
    """Middleware that adds security-related HTTP headers to responses.

    Adds headers to prevent XSS attacks, clickjacking, and MIME type sniffing,
    while also implementing strict referrer policy and removing server identification.
    """

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if "Server" in response:
            del response["Server"]

        return response
