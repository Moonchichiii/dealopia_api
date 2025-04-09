"""Hash utilities for message and secret handling.

This module provides functions to hash and verify messages and secrets using
HMAC-SHA256 and SHA-256 algorithms with optional salting and peppering.
"""

import hashlib
import hmac
import os

# Pepper value from environment or default
PEPPER = os.getenv("HASH_PEPPER", "default_pepper_value")


def hash_message(message: str) -> str:
    """Hash a message using HMAC-SHA256 with pepper.

    Args:
        message (str): The message string to hash.

    Returns:
        str: A hexadecimal string representing the hash.

    Raises:
        ValueError: If message is not a string.
    """
    if not isinstance(message, str):
        raise ValueError("Message must be a string.")

    message_bytes = message.encode("utf-8")
    pepper_bytes = PEPPER.encode("utf-8")

    return hmac.new(pepper_bytes, message_bytes, hashlib.sha256).hexdigest()


def hash_secret(secret: str, salt: str | None = None) -> str:
    """Hash a secret using SHA-256 with optional salt.

    Args:
        secret (str): The secret string to hash.
        salt (str | None): Optional salt string to add to the hash.

    Returns:
        str: A hexadecimal string representing the hash.

    Raises:
        ValueError: If secret is not a string.
    """
    if not isinstance(secret, str):
        raise ValueError("Secret must be a string.")

    if salt is None:
        salt = os.urandom(16).hex()

    secret_bytes = f"{secret}{salt}".encode("utf-8")
    return hashlib.sha256(secret_bytes).hexdigest()


def verify_message_hash(message: str, message_hash: str) -> bool:
    """Verify if a message matches its hash.

    Args:
        message (str): The original message string.
        message_hash (str): The expected hash string.

    Returns:
        bool: True if the message matches the hash, False otherwise.

    Raises:
        ValueError: If either argument is not a string.
    """
    if not isinstance(message, str) or not isinstance(message_hash, str):
        raise ValueError("Both message and message_hash must be strings.")

    calculated_hash = hash_message(message)
    return hmac.compare_digest(calculated_hash, message_hash)