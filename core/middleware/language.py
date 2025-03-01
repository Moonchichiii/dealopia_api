from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

class UserLanguageMiddleware(MiddlewareMixin):
    """Middleware to set language based on user preferences"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                user_language = request.user.preferred_language
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language
            except:
                pass
