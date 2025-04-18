# Standard library imports
import base64
import io
import logging
from uuid import UUID

# Third-party imports
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
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

logger = logging.getLogger(__name__)
User = get_user_model()


def create_error_response(message, status_code):
    """Create a consistent error response."""
    return Response({"error": _(message)}, status=status_code)


def create_success_response(data=None, message=None):
    """Create a consistent success response."""
    response_data = {"success": True}
    if message:
        response_data["message"] = _(message)
    if data:
        response_data.update(data)
    return Response(response_data)


def get_user_or_none(user_id):
    """Get user by ID or return None if not found or invalid UUID."""
    try:
        return User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError):
        return None


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view checking for 2FA."""

    @extend_schema(
        description="Login with email and password, may require 2FA if enabled"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        # Check if 2FA is required
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return Response(
                {
                    "requires_2fa": True,
                    "user_id": str(user.id),
                    "message": _("Two-factor authentication required"),
                }
            )

        # 2FA not required, proceed with normal authentication
        response = Response(serializer.validated_data)

        # Set cookies directly - using your settings
        cookie_settings = getattr(settings, "SIMPLE_JWT", {})
        access_cookie = cookie_settings.get("AUTH_COOKIE")
        refresh_cookie = cookie_settings.get("AUTH_COOKIE_REFRESH")

        if access_cookie:
            response.set_cookie(
                access_cookie,
                serializer.validated_data["access"],
                httponly=True,
                samesite=cookie_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
                secure=cookie_settings.get("AUTH_COOKIE_SECURE", False),
                path=cookie_settings.get("AUTH_COOKIE_PATH", "/"),
                domain=cookie_settings.get("AUTH_COOKIE_DOMAIN", None),
            )

        if refresh_cookie:
            response.set_cookie(
                refresh_cookie,
                serializer.validated_data["refresh"],
                httponly=True,
                samesite=cookie_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
                secure=cookie_settings.get("AUTH_COOKIE_SECURE", False),
                path=cookie_settings.get("AUTH_COOKIE_PATH", "/"),
                domain=cookie_settings.get("AUTH_COOKIE_DOMAIN", None),
            )

        return response


class TwoFactorVerifyView(APIView):
    """Verify a TOTP code for two-factor authentication."""

    permission_classes = []

    @extend_schema(
        description="Verify a TOTP code for two-factor authentication",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "format": "uuid"},
                    "token": {"type": "string", "description": "6-digit code"},
                },
                "required": ["user_id", "token"],
            }
        },
        responses={
            200: OpenApiResponse(description="Verified, returns JWT tokens"),
            400: OpenApiResponse(description="Invalid code or missing data"),
            404: OpenApiResponse(description="User not found or no 2FA device"),
        },
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        token = request.data.get("token")
        if not user_id or not token:
            return create_error_response(
                "User ID and token are required.", status.HTTP_400_BAD_REQUEST
            )
        user = get_user_or_none(user_id)
        if not user:
            return create_error_response("User not found.", status.HTTP_404_NOT_FOUND)
        try:
            device = TOTPDevice.objects.get(user=user, confirmed=True)
        except TOTPDevice.DoesNotExist:
            return create_error_response(
                "No confirmed 2FA device found for this user.",
                status.HTTP_404_NOT_FOUND,
            )
        if not device.verify_token(token):
            return create_error_response(
                "Invalid verification code.", status.HTTP_400_BAD_REQUEST
            )
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        refresh = RefreshToken.for_user(user)
        return Response(
            {"refresh": str(refresh), "access": str(refresh.access_token)}
        )


class TwoFactorSetupView(APIView):
    """Setup two-factor authentication for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Generate a TOTP setup QR code and secret for the authenticated user.",
        responses={
            200: OpenApiResponse(
                description="Returns setup details including QR code."
            ),
            400: OpenApiResponse(description="User already has 2FA enabled."),
        },
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return create_error_response(
                "Two-factor authentication is already enabled.",
                status.HTTP_400_BAD_REQUEST,
            )
        device, created = TOTPDevice.objects.get_or_create(
            user=user,
            confirmed=False,
            defaults={"name": f"{user.email}'s device"},
        )
        if not created:
            device.key = TOTPDevice.random_key()
            device.save()
        key_b32 = base64.b32encode(device.bin_key).decode("utf-8")
        totp = pyotp.TOTP(key_b32)
        provision_uri = totp.provisioning_uri(
            name=user.email, issuer_name="Dealopia"
        )
        img = qrcode.make(provision_uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return Response(
            {
                "qr_code": f"data:image/png;base64,{qr_code_b64}",
                "secret": key_b32,
                "instructions": _(
                    "Scan QR code with your authenticator app or enter the secret key."
                ),
            }
        )

    @extend_schema(
        description="Confirm and enable 2FA setup with a verification code.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "6-digit code"}
                },
                "required": ["token"],
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully enabled."),
            400: OpenApiResponse(description="Invalid verification code."),
            404: OpenApiResponse(description="No pending 2FA setup found."),
        },
    )
    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            return create_error_response(
                "Verification code is required.", status.HTTP_400_BAD_REQUEST
            )
        try:
            device = TOTPDevice.objects.get(user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            return create_error_response(
                "No pending two-factor setup found.", status.HTTP_404_NOT_FOUND
            )
        if not device.verify_token(token):
            return create_error_response(
                "Invalid verification code.", status.HTTP_400_BAD_REQUEST
            )
        device.confirmed = True
        device.save()
        return create_success_response(
            message="Two-factor authentication enabled successfully."
        )


class TwoFactorDisableView(APIView):
    """Disable two-factor authentication for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Disable 2FA (requires password confirmation).",
        request={
            "application/json": {
                "type": "object",
                "properties": {"password": {"type": "string"}},
                "required": ["password"],
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully disabled."),
            400: OpenApiResponse(
                description="Invalid password or missing confirmation."
            ),
            404: OpenApiResponse(description="User has no 2FA enabled."),
        },
    )
    def post(self, request, *args, **kwargs):
        password = request.data.get("password")
        if not password:
            return create_error_response(
                "Password confirmation is required.", status.HTTP_400_BAD_REQUEST
            )
        if not request.user.check_password(password):
            return create_error_response(
                "Invalid password.", status.HTTP_400_BAD_REQUEST
            )
        deleted_count, _ = TOTPDevice.objects.filter(user=request.user).delete()
        if deleted_count == 0:
            return create_error_response(
                "Two-factor authentication is not enabled.",
                status.HTTP_404_NOT_FOUND,
            )
        return create_success_response(
            message="Two-factor authentication disabled successfully."
        )


class SessionInfoView(APIView):
    """Get information about the current authenticated session."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get current session details including 2FA status.",
        responses={200: OpenApiResponse(description="Returns session details.")},
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        simple_jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        access_token_lifetime = simple_jwt_settings.get("ACCESS_TOKEN_LIFETIME")
        token_expires_in = (
            int(access_token_lifetime.total_seconds())
            if access_token_lifetime
            else 1800
        )
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
    """Handle user logout by blacklisting tokens and clearing session/cookies."""

    # This is the key change - allow unauthenticated access for logout
    permission_classes = []
    authentication_classes = []  # Don't require authentication

    def post(self, request, *args, **kwargs):
        user_id = None

        # Only try to get user ID and blacklist tokens if the user is authenticated
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
            logger.info(f"Logout requested for user: {user_id}")

            try:
                # Blacklist all tokens for this user
                tokens = OutstandingToken.objects.filter(user_id=user_id)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)

                # Flush the Django session
                if hasattr(request, "session"):
                    request.session.flush()
            except Exception as e:
                logger.error(f"Error during logout for user {user_id}: {e}")
        else:
            logger.info("Logout requested for unauthenticated user")

        # Create response
        response = Response(
            {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
        )

        # Get cookie settings from Django settings
        cookie_path = getattr(settings, "SESSION_COOKIE_PATH", "/")
        cookie_domain = getattr(settings, "SESSION_COOKIE_DOMAIN", None)

        # Clear auth cookies using Django's delete_cookie method
        jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        access_cookie = jwt_settings.get("AUTH_COOKIE")
        refresh_cookie = jwt_settings.get("AUTH_COOKIE_REFRESH")

        # Clear all potential auth cookies with exact same settings they were created with
        cookies_to_clear = ["sessionid", "csrftoken"]

        if access_cookie:
            cookies_to_clear.append(access_cookie)
        if refresh_cookie:
            cookies_to_clear.append(refresh_cookie)

        # Explicitly add the exact cookie names seen in the browser
        cookies_to_clear.extend(["auth-token", "refresh-token"])

        for cookie_name in cookies_to_clear:
            # Try with specific domain
            response.delete_cookie(
                cookie_name, path=cookie_path, domain=cookie_domain
            )

            # Also try with localhost domain specifically
            response.delete_cookie(
                cookie_name, path=cookie_path, domain="localhost"
            )

            # Try with root path
            response.delete_cookie(cookie_name, path="/")

            # Try with both localhost and root path
            response.delete_cookie(cookie_name, path="/", domain="localhost")

        # Set cache control headers to prevent caching
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        if user_id:
            logger.info(f"Logout successful for user {user_id}")
        else:
            logger.info("Logout successful for unauthenticated user")

        return response


class TokenRefreshRateLimitedView(APIView):
    """Custom token refresh view with rate limiting and security checks."""

    permission_classes = []
    throttle_scope = "token_refresh"

    @extend_schema(
        description="Refresh an expired access token using a refresh token.",
        request={
            "application/json": {
                "type": "object",
                "properties": {"refresh": {"type": "string"}},
                "required": ["refresh"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="Returns new access token (and optionally refresh)."
            ),
            400: OpenApiResponse(description="Refresh token missing."),
            401: OpenApiResponse(
                description="Invalid, expired, or blacklisted refresh token."
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token_str = request.data.get("refresh")
        simple_jwt_settings = getattr(settings, "SIMPLE_JWT", {})
        refresh_cookie_name = simple_jwt_settings.get("AUTH_COOKIE_REFRESH")
        if not refresh_token_str and refresh_cookie_name:
            refresh_token_str = request.COOKIES.get(refresh_cookie_name)
        if not refresh_token_str:
            return create_error_response(
                "Refresh token is required.", status.HTTP_400_BAD_REQUEST
            )
        try:
            refresh_token = RefreshToken(refresh_token_str)
            user_id = refresh_token.payload.get("user_id")
            user = User.objects.get(id=user_id)
            if not user.is_active:
                logger.warning(f"Refresh attempt for inactive user: {user_id}")
                return create_error_response(
                    "User account is disabled.", status.HTTP_401_UNAUTHORIZED
                )
            jti = refresh_token.payload.get("jti")
            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                logger.warning(
                    f"Refresh attempt with blacklisted token (jti: {jti}) for user: {user_id}"
                )
                return create_error_response(
                    "Token is blacklisted.", status.HTTP_401_UNAUTHORIZED
                )
            response_data = {"access": str(refresh_token.access_token)}
            rotate_tokens = simple_jwt_settings.get("ROTATE_REFRESH_TOKENS", False)
            blacklist_after_rotation = simple_jwt_settings.get(
                "BLACKLIST_AFTER_ROTATION", False
            )
            if rotate_tokens:
                if blacklist_after_rotation:
                    try:
                        token = OutstandingToken.objects.get(jti=jti)
                        BlacklistedToken.objects.get_or_create(token=token)
                        logger.info(
                            f"Blacklisted old refresh token (jti: {jti}) after rotation for user: {user_id}"
                        )
                    except OutstandingToken.DoesNotExist:
                        logger.warning(
                            f"Could not find OutstandingToken (jti: {jti}) to blacklist after rotation."
                        )
                    except Exception as e:
                        logger.error(
                            f"Error blacklisting token (jti: {jti}) after rotation: {e}"
                        )
                response_data["refresh"] = str(refresh_token)
            response = Response(response_data)
            access_cookie_name = simple_jwt_settings.get("AUTH_COOKIE")
            cookie_samesite = simple_jwt_settings.get(
                "AUTH_COOKIE_SAMESITE", "Lax"
            )
            cookie_secure = simple_jwt_settings.get("AUTH_COOKIE_SECURE", False)
            cookie_path = simple_jwt_settings.get("AUTH_COOKIE_PATH", "/")
            cookie_domain = simple_jwt_settings.get("AUTH_COOKIE_DOMAIN", None)
            if access_cookie_name:
                response.set_cookie(
                    access_cookie_name,
                    response_data["access"],
                    httponly=True,
                    samesite=cookie_samesite,
                    secure=cookie_secure,
                    path=cookie_path,
                    domain=cookie_domain,
                )
            if (
                rotate_tokens
                and refresh_cookie_name
                and "refresh" in response_data
            ):
                response.set_cookie(
                    refresh_cookie_name,
                    response_data["refresh"],
                    httponly=True,
                    samesite=cookie_samesite,
                    secure=cookie_secure,
                    path=cookie_path,
                    domain=cookie_domain,
                )
            return response
        except (TokenError, User.DoesNotExist, ValueError) as e:
            logger.warning(f"Token refresh failed: {e}")
            return create_error_response(
                "Invalid or expired refresh token.", status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during token refresh: {e}", exc_info=True
            )
            return create_error_response(
                "An unexpected error occurred.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SocialAuthCallbackView(APIView):
    """Handle social auth callbacks, issue JWT tokens, and redirect."""

    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            logger.warning(
                "Social auth callback failed: User not authenticated."
            )
            error_url = f"{settings.FRONTEND_URL}/auth/error?message=AuthenticationFailed"
            return redirect(error_url)
        logger.info(
            f"Social auth callback successful for user: {request.user.id}"
        )
        refresh = RefreshToken.for_user(request.user)
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access={str(refresh.access_token)}&refresh={str(refresh)}"
        return redirect(redirect_url)
