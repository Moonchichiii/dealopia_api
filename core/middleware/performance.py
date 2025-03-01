import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('dealopia.performance')

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to log slow requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log requests that take more than 1 second
            if duration > 1:
                logger.warning(
                    f'Slow request: {request.method} {request.path} '
                    f'({duration:.2f}s)'
                )
            
            # Add the processing time to the response headers
            response['X-Processing-Time'] = f'{duration:.2f}s'
            
        return response
