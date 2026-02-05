import os
import logging
import json
from typing import Any, Dict, List, Optional

import openai
from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape
from rest_framework.exceptions import APIException
from langdetect import detect_langs

from apps.chatbot.hash import hash_message
from apps.chatbot.models import Chatbot, Message

logger = logging.getLogger(__name__)
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def get_cached_response(user_message: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Optional[Dict[str, Any]]:
    # (as defined previously)
    location_str = f"_{latitude}_{longitude}" if latitude and longitude else ""
    cache_key = f"dealopia_chatbot_response_{hash_message(user_message)}{location_str}"
    cached_response = cache.get(cache_key)
    logger.info(
        "Cache %s for message: %s",
        "hit" if cached_response else "miss",
        user_message,
    )
    return cached_response

def set_cached_response(user_message: str, response: Dict[str, Any], latitude: Optional[float] = None, longitude: Optional[float] = None) -> None:
    location_str = f"_{latitude}_{longitude}" if latitude and longitude else ""
    cache_key = f"dealopia_chatbot_response_{hash_message(user_message)}{location_str}"
    cache.set(cache_key, response, timeout=3600)  # Cache for 1 hour

def detect_language(user_message: str) -> str:
    if len(user_message) <= 2:
        return "en"
    try:
        detected_languages = detect_langs(user_message)
        logger.info('Language detection results for "%s": %s', user_message, detected_languages)
        for lang in detected_languages:
            if lang.prob > 0.5:
                logger.info(f"Detected language: {lang.lang} ({lang.prob})")
                return lang.lang
    except (ValueError, TypeError) as e:
        logger.error("Language detection failed: %s", e)
    logger.info("Defaulting to English for message: %s", user_message)
    return "en"

def _get_system_prompt(language: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
    location_context = f" The user's current coordinates are: latitude {latitude}, longitude {longitude}." if latitude and longitude else ""
    if language == "sv":
        return (
            "Du är en chatbot för Dealopia, en plattform för platsbaserad hållbar shopping. "
            "Dealopia hjälper användare att hitta miljövänliga produkter och erbjudanden i deras närhet. "
            f"{location_context}"
            "Du ska hjälpa användarna med att:"
            "1. Förstå Dealopias fokus på hållbar shopping."
            "2. Hitta hållbara butiker, produkter och erbjudanden baserat på deras plats."
            "3. Navigera i plattformen och förstå olika produktkategorier och hållbarhetsmätvärden."
            "4. Få vägledning om butiks-/produkthantering via Wagtail CMS (för butiksägare)."
            "5. Besvara vanliga frågor om plattformen, hållbarhetscertifieringar, etc."
            "6. Hjälpa användare att förfina sökningar efter specifika produkter/kategorier."
            "7. Klargöra att butiksägare hanterar sitt eget lager och erbjudanden."
            "Var koncis, relevant och hjälpsam."
        )
    return (
        "You are a chatbot for Dealopia, a location-based sustainable shopping platform. "
        "Dealopia helps users discover eco-friendly products and deals in their vicinity. "
        f"{location_context}"
        "You should assist users with:"
        "1. Understanding Dealopia's focus on sustainable shopping."
        "2. Finding sustainable shops, products, and deals based on their location."
        "3. Navigating the platform and understanding different product categories and sustainability metrics."
        "4. Getting guidance on shop/product management through Wagtail CMS (for shop owners)."
        "5. Answering common questions about the platform, sustainability certifications, etc."
        "6. Helping users refine searches for specific products/categories."
        "7. Clarifying that shop owners manage their own inventory and deals."
        "Be concise, relevant, and helpful."
    )

def _get_openai_response(message: str, system_prompt: str):
    function_description = {
        "name": "suggest_actions",
        "description": "Suggest relevant actions the user might want to take based on their query",
        "parameters": {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "description": "List of suggested actions the user can take",
                    "items": {
                        "type": "string",
                        "description": "A specific action the user might want to take"
                    }
                }
            },
            "required": ["actions"]
        }
    }
    return client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        functions=[function_description],
        function_call="auto",
        max_tokens=300,
        temperature=0.3,
    )

class OpenAIServiceError(APIException):
    status_code = 503
    default_detail = "OpenAI service error"

class ChatbotService:
    """Service class to handle interactions with the OpenAI API for Dealopia chatbot."""
    @staticmethod
    def process_chatbot_request(validated_data: Dict[str, Any]) -> Dict[str, Any]:
        user_message = validated_data.get("message", "").strip()
        user_id = validated_data.get("user_id")
        latitude = validated_data.get("latitude")
        longitude = validated_data.get("longitude")
        if not user_message:
            return {"message": "Please enter a message to get a response."}
        safe_user_message = escape(user_message)
        cached_response = get_cached_response(safe_user_message, latitude, longitude)
        if cached_response:
            return cached_response
        try:
            detected_language = detect_language(safe_user_message)
            logger.info("Detected language: %s", detected_language)
            system_prompt = _get_system_prompt(detected_language, latitude, longitude)
            response = _get_openai_response(safe_user_message, system_prompt)
            bot_message = response.choices[0].message.content
            suggested_actions = []
            if response.choices[0].message.function_call:
                function_args = json.loads(response.choices[0].message.function_call.arguments)
                suggested_actions = function_args.get("actions", [])
            result = {
                "message": bot_message.strip() if bot_message else "",
                "suggested_actions": suggested_actions
            }
            if user_id:
                try:
                    chatbot_obj, _ = Chatbot.objects.get_or_create(name="Dealopia Assistant")
                    Message.objects.create(
                        user_id=user_id,
                        chatbot=chatbot_obj,
                        user_message=safe_user_message,
                        bot_response=bot_message,
                        status="SUCCESS"
                    )
                except Exception as e:
                    logger.error("Failed to save message to database: %s", e)
            set_cached_response(safe_user_message, result, latitude, longitude)
            return result
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            if user_id:
                try:
                    chatbot_obj, _ = Chatbot.objects.get_or_create(name="Dealopia Assistant")
                    Message.objects.create(
                        user_id=user_id,
                        chatbot=chatbot_obj,
                        user_message=safe_user_message,
                        bot_response="Error processing request",
                        status="ERROR"
                    )
                except Exception as db_error:
                    logger.error("Failed to save error message to database: %s", db_error)
            raise OpenAIServiceError(detail=str(e))
