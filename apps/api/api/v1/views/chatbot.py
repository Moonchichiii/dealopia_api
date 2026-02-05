import logging
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


from api.v1.serializers.chatbot import ChatbotRequestSerializer, ChatbotResponseSerializer
from apps.chatbot.services import ChatbotService, OpenAIServiceError


logger = logging.getLogger(__name__)


class ChatbotAnonRateThrottle(AnonRateThrottle):
    rate = '5/minute'


class ChatbotUserRateThrottle(UserRateThrottle):
    rate = '15/minute'


@csrf_protect
@api_view(["POST"])
@throttle_classes([ChatbotAnonRateThrottle, ChatbotUserRateThrottle])
@permission_classes([AllowAny])
def dealopia_chatbot(request):
    """
    Chatbot endpoint for Dealopia:


    Accepts:
      - message: User's question/input
      - latitude/longitude: Optional coordinates
      - language (optional): ISO code for language (e.g., "en", "es", "fr", "de")


    Returns:
      - message: Bot's response
      - suggested_actions: A list of suggested next steps
    """
    request_data = request.data.copy()
    request_data['user_id'] = request.user.id if request.user.is_authenticated else None


    serializer = ChatbotRequestSerializer(data=request_data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=400)
   
    try:
        result = ChatbotService.process_chatbot_request(serializer.validated_data)
        response_serializer = ChatbotResponseSerializer(data=result)
        if response_serializer.is_valid():
            return Response(response_serializer.data, status=200)
        else:
            return Response({"error": response_serializer.errors}, status=500)
    except OpenAIServiceError as e:
        logger.error("OpenAI service error: %s", str(e))
        return Response({"error": "Our assistant is currently unavailable. Please try again later."}, status=503)
    except Exception as e:
        logger.error("Unexpected error in chatbot view: %s", str(e))
        return Response({"error": "An unexpected error occurred. Please try again later."}, status=500)