import logging
import re
import time

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("dealopia.performance")


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to log slow requests with optimizations to avoid
    unnecessary overhead for static files and other fast routes.
    """

    EXCLUDE_PATTERNS = [
        r"^/static/",
        r"^/media/",
        r"^/favicon\.ico$",
        r"^/robots\.txt$",
        r"^/__debug__/",
        r"^/admin/jsi18n/",
    ]

    SLOW_REQUEST_THRESHOLD = getattr(settings, "SLOW_REQUEST_THRESHOLD", 1.0)

    def __init__(self, get_response):
        super().__init__(get_response)
        self.exclude_patterns = [
            re.compile(pattern) for pattern in self.EXCLUDE_PATTERNS
        ]
        self.track_performance = not settings.DEBUG or getattr(
            settings, "TRACK_PERFORMANCE_IN_DEBUG", False
        )

    def should_track_path(self, path):
        """Check if the path should be tracked for performance"""
        return not any(pattern.match(path) for pattern in self.exclude_patterns)

    def process_request(self, request):
        """Add start_time to requests that should be tracked"""
        if not self.track_performance:
            return

        if self.should_track_path(request.path):
            request.start_time = time.time()

    def process_response(self, request, response):
        """Calculate and log the response time for slow requests"""
        if not hasattr(request, "start_time"):
            return response

        duration = time.time() - request.start_time
        response["X-Processing-Time"] = f"{duration:.2f}s"

        if duration < self.SLOW_REQUEST_THRESHOLD:
            return response

        log_data = {
            "path": request.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration": f"{duration:.2f}s",
            "user": request.user.id if request.user.is_authenticated else "anonymous",
        }

        if "REMOTE_ADDR" in request.META:
            log_data["ip"] = request.META["REMOTE_ADDR"]

        if "HTTP_USER_AGENT" in request.META:
            log_data["user_agent"] = request.META["HTTP_USER_AGENT"]

        if request.GET:
            safe_params = {
                k: v
                for k, v in request.GET.items()
                if k.lower() not in ["password", "token", "key"]
            }
            if safe_params:
                log_data["query_params"] = safe_params

        logger.warning(
            f"Slow request: {request.method} {request.path} ({duration:.2f}s)",
            extra=log_data,
        )

        if duration >= self.SLOW_REQUEST_THRESHOLD * 5:
            logger.error(
                f"Very slow request: {request.method} {request.path} ({duration:.2f}s)",
                extra=log_data,
            )

        return response
