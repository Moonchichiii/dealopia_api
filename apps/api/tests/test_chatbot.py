import json
from unittest.mock import patch, MagicMock

from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase


class ChatbotTests(APITestCase):
    def setUp(self):
        # Clear the cache before each test to prevent cross-test interference
        cache.clear()

    @patch("apps.chatbot.services._get_openai_response")
    def test_chatbot_valid_message(self, mock_get_openai_response):
        """
        Test that a valid message returns an OpenAI-generated response.
        The OpenAI API call is mocked to avoid making real API calls.
        """
        # Configure a fake response from OpenAI
        fake_response = MagicMock()
        fake_choice = MagicMock()
        fake_message = MagicMock(content="Test response from chatbot")
        # Optionally, simulate no function_call (i.e., no suggested actions)
        fake_choice.message = fake_message
        fake_response.choices = [fake_choice]
        mock_get_openai_response.return_value = fake_response

        url = reverse("chatbot")
        payload = {"message": "What sustainable deals are available?"}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Test response from chatbot")
        self.assertIn("suggested_actions", response.data)
        self.assertEqual(response.data["suggested_actions"], [])

    def test_chatbot_empty_message(self):
        """
        Test that an empty message returns a prompt to enter a message.
        """
        url = reverse("chatbot")
        payload = {"message": ""}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expect the default response for empty input.
        self.assertEqual(response.data.get("message"),
                         "Please enter a message to get a response.")

    @patch("apps.chatbot.services._get_openai_response")
    def test_chatbot_caching(self, mock_get_openai_response):
        """
        Test that when the same chatbot query (with the same message and location)
        is sent twice, the second call returns the cached response.
        The OpenAI API is called only once.
        """
        fake_response = MagicMock()
        fake_choice = MagicMock()
        fake_message = MagicMock(content="Cached response")
        fake_choice.message = fake_message
        fake_response.choices = [fake_choice]
        mock_get_openai_response.return_value = fake_response

        url = reverse("chatbot")
        payload = {
            "message": "Test caching",
            "latitude": 40.7128,
            "longitude": -74.0060
        }

        # First API call: should be a cache miss and trigger the OpenAI call.
        response1 = self.client.post(url, payload, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["message"], "Cached response")

        # Second API call with the same payload: should hit the cache.
        response2 = self.client.post(url, payload, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["message"], "Cached response")

        # Verify that _get_openai_response was only invoked once.
        self.assertEqual(mock_get_openai_response.call_count, 1)
