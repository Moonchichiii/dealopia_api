"""Models for chatbot application handling messages and bot interactions."""

from django.conf import settings
from django.db import models

from .hash import hash_message


class Chatbot(models.Model):
    """Represents a chatbot entity.

    Attributes:
        name (str): The name of the chatbot.
        created_at (datetime): Timestamp of chatbot creation.
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        app_label = "chatbot"



class Message(models.Model):
    """Stores chat messages between users and chatbots.

    Attributes:
        user (ForeignKey): Reference to the user who sent the message.
        chatbot (ForeignKey): Reference to the chatbot that processed the message.
        user_message (str): The message sent by the user.
        bot_response (str): The response generated by the chatbot.
        user_message_hash (str): Hash of the user's message for verification.
        timestamp (datetime): When the message was created.
        status (str): Current status of the message processing.
    """

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("ERROR", "Error"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    chatbot = models.ForeignKey("Chatbot", on_delete=models.CASCADE)
    user_message = models.TextField()
    bot_response = models.TextField(blank=True, null=True)
    user_message_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)

    class Meta:
        """Meta configuration for Message model."""

        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        """Returns a formatted string with message timestamp."""
        return f"Message at {self.timestamp}"

    def save(self, *args, **kwargs) -> None:
        """Generates message hash before saving."""
        if not self.user_message_hash:
            self.user_message_hash = hash_message(self.user_message)
        super().save(*args, **kwargs)