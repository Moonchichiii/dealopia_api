import base64
import io
import logging
from uuid import UUID

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

logger = logging.getLogger(__name__)
User = get_user_model()


def create_error_response(message, status_code):
    """Helper to create consistent error responses"""
    return Response({"error": _(message)}, status=status_code)


def create_success_response(data=None, message=None):
    """Helper to create consistent success responses"""
    response_data = {"success": True}
    if message:
        response_data["message"] = _(message)
    if data:
        response_data.update(data)
    return Response(response_data)


def get_user_or_404(user_id):
    """Get user by ID or raise 404"""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


class CustomTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        description="Login with email and password, may require 2FA if enabled"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=request.data.get("email"))
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return Response(
                {
                    "requires_2fa": True,
                    "user_id": str(user.id),
                    "message": _("Two-factor authentication required"),
                }
            )

        return Response(serializer.validated_data)


class TwoFactorVerifyView(APIView):
    """Verify a TOTP code for two-factor authentication"""

    permission_classes = []

    @extend_schema(
        description="Verify a TOTP code for two-factor authentication",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "User ID",
                    },
                    "token": {
                        "type": "string",
                        "description": "TOTP token (6-digit code)",
                    },
                },
                "required": ["user_id", "token"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="Successfully verified, returns JWT tokens"
            ),
            400: OpenApiResponse(
                description="Invalid verification code or missing data"
            ),
            404: OpenApiResponse(
                description="User not found or no 2FA device configured"
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        token = request.data.get("token")

        if not user_id or not token:
            return create_error_response(
                "Both user_id and token are required", status.HTTP_400_BAD_REQUEST
            )

        user = get_user_or_404(user_id)
        if not user:
            return create_error_response("User not found", status.HTTP_404_NOT_FOUND)

        try:
            device = TOTPDevice.objects.get(user=user, confirmed=True)
        except TOTPDevice.DoesNotExist:
            return create_error_response(
                "No 2FA device configured for this user", status.HTTP_404_NOT_FOUND
            )

        if not device.verify_token(token):
            return create_error_response(
                "Invalid verification code", status.HTTP_400_BAD_REQUEST
            )

        # Record successful 2FA login
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )


class TwoFactorSetupView(APIView):
    """Setup two-factor authentication for a user"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Generate a TOTP setup for the authenticated user",
        responses={
            200: OpenApiResponse(description="Returns setup details including QR code"),
            400: OpenApiResponse(description="User already has 2FA enabled"),
        },
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return create_error_response(
                "Two-factor authentication is already enabled",
                status.HTTP_400_BAD_REQUEST,
            )

        device, created = TOTPDevice.objects.get_or_create(
            user=user, confirmed=False, defaults={"name": f"{user.email}'s device"}
        )

        if not created:
            device.key = TOTPDevice.random_key()
            device.save()

        key = device.bin_key
        totp = pyotp.TOTP(base64.b32encode(key).decode("utf-8"))

        provision_uri = totp.provisioning_uri(name=user.email, issuer_name="Dealopia")

        img = qrcode.make(provision_uri)
        buffer = io.BytesIO()
        img.save(buffer)
        qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return Response(
            {
                "qr_code": f"data:image/png;base64,{qr_code}",
                "secret": base64.b32encode(key).decode("utf-8"),
                "instructions": _(
                    "Scan this QR code with your authenticator app, or enter the secret key manually."
                ),
            }
        )

    @extend_schema(
        description="Confirm and enable 2FA setup with a verification code",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "TOTP token (6-digit code)",
                    },
                },
                "required": ["token"],
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully enabled"),
            400: OpenApiResponse(description="Invalid verification code"),
            404: OpenApiResponse(description="No pending 2FA setup found"),
        },
    )
    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            return create_error_response(
                "Verification code is required", status.HTTP_400_BAD_REQUEST
            )

        try:
            device = TOTPDevice.objects.get(user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            return create_error_response(
                "No pending two-factor setup found", status.HTTP_404_NOT_FOUND
            )

        if not device.verify_token(token):
            return create_error_response(
                "Invalid verification code", status.HTTP_400_BAD_REQUEST
            )

        device.confirmed = True
        device.save()

        return create_success_response(
            message="Two-factor authentication has been enabled successfully"
        )


class TwoFactorDisableView(APIView):
    """Disable two-factor authentication for a user"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Disable 2FA for the authenticated user (requires password confirmation)",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "password": {
                        "type": "string",
                        "description": "User password for confirmation",
                    },
                },
                "required": ["password"],
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully disabled"),
            400: OpenApiResponse(
                description="Invalid password or missing confirmation"
            ),
            404: OpenApiResponse(description="User has no 2FA enabled"),
        },
    )
    def post(self, request, *args, **kwargs):
        password = request.data.get("password")
        if not password:
            return create_error_response(
                "Password confirmation is required", status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(password):
            return create_error_response(
                "Invalid password", status.HTTP_400_BAD_REQUEST
            )

        devices = TOTPDevice.objects.filter(user=request.user)
        if not devices.exists():
            return create_error_response(
                "Two-factor authentication is not enabled for this user",
                status.HTTP_404_NOT_FOUND,
            )

        devices.delete()

        return create_success_response(
            message="Two-factor authentication has been disabled successfully"
        )


class SessionInfoView(APIView):
    """Get information about the current authenticated session"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get information about the current authenticated session",
        responses={
            200: OpenApiResponse(
                description="Returns session details including 2FA status"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        token_expires_in = 1800  # 30 minutes in seconds

        return Response(
            {
                "user_id": str(user.id),
                "email": user.email,
                "has_2fa_enabled": has_2fa,
                "token_expires_in": token_expires_in,
                "last_login": user.last_login,
            }
        )


class LogoutView(APIView):
    """Handle user logout completely by blacklisting tokens and clearing session"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Logout the current user, blacklist tokens, and clear session",
        responses={
            200: OpenApiResponse(description="Successfully logged out"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    def post(self, request, *args, **kwargs):
        logger.info(f"Logout requested for user: {request.user.id}")

        try:
            # Blacklist the user's tokens to prevent reuse
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            logger.error(f"Error blacklisting tokens: {e}")

        try:
            # Handle session invalidation
            if hasattr(request, "session"):
                request.session.flush()
        except Exception as e:
            logger.error(f"Error flushing session: {e}")

        # Create response and delete cookies
        response = Response(
            {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
        )

        # Clear all cookies that might be storing auth state
        auth_cookies = [
            "sessionid",
            "csrftoken",
            "refresh_token",
            "access_token",
            "auth-token",
            "refresh-token",
        ]

        for cookie_name in auth_cookies:
            response.delete_cookie(
                cookie_name,
                path="/",
                domain=None,
                samesite="Lax",
            )

        return response


class TokenRefreshRateLimitedView(APIView):
    """Custom token refresh view with rate limiting to prevent abuse"""

    permission_classes = []
    throttle_scope = "token_refresh"

    @extend_schema(
        description="Refresh an expired access token",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string", "description": "Refresh token"},
                },
                "required": ["refresh"],
            }
        },
        responses={
            200: OpenApiResponse(description="Returns new access token"),
            401: OpenApiResponse(description="Invalid or expired refresh token"),
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return create_error_response(
                "Refresh token is required", status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.payload.get("user_id")
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return create_error_response(
                    "User account is disabled", status.HTTP_401_UNAUTHORIZED
                )

            return Response({"access": str(refresh.access_token)})

        except (TokenError, User.DoesNotExist):
            return create_error_response(
                "Invalid or expired refresh token", status.HTTP_401_UNAUTHORIZED
            )


class SocialAuthCallbackView(APIView):
    """Handle social authentication callbacks and return JWT tokens"""

    permission_classes = []

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return create_error_response(
                "Authentication failed", status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(request.user)
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access={str(refresh.access_token)}&refresh={str(refresh)}"

        return redirect(redirect_url)
