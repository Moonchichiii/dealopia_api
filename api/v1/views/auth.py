# api/v1/views/auth.py - Enhanced authentication views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import pyotp
import qrcode
import io
import base64
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from api.v1.serializers.accounts import UserSerializer

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Enhanced token obtain view that handles 2FA requirements
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
            
        # Check if user has 2FA enabled
        user = User.objects.get(email=request.data.get('email'))
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            # Return user_id instead of tokens if 2FA is required
            return Response({
                'requires_2fa': True,
                'user_id': str(user.id),
                'message': _('Two-factor authentication required')
            })
            
        # No 2FA required, return tokens
        return Response(serializer.validated_data)

class TwoFactorVerifyView(APIView):
    """
    Verify a TOTP code for two-factor authentication
    """
    permission_classes = []
    
    @extend_schema(
        description="Verify a TOTP code for two-factor authentication",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'format': 'uuid', 'description': 'User ID'},
                    'token': {'type': 'string', 'description': 'TOTP token (6-digit code)'},
                },
                'required': ['user_id', 'token']
            }
        },
        responses={
            200: OpenApiResponse(description="Successfully verified, returns JWT tokens"),
            400: OpenApiResponse(description="Invalid verification code or missing data"),
            404: OpenApiResponse(description="User not found or no 2FA device configured"),
        }
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        token = request.data.get('token')
        
        if not user_id or not token:
            return Response(
                {'error': _('Both user_id and token are required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            device = TOTPDevice.objects.get(user=user, confirmed=True)
            
            if device.verify_token(token):
                # Record successful 2FA login
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                return Response(
                    {'error': _('Invalid verification code')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': _('User not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        except TOTPDevice.DoesNotExist:
            return Response(
                {'error': _('No 2FA device configured for this user')},
                status=status.HTTP_404_NOT_FOUND
            )

class TwoFactorSetupView(APIView):
    """
    Setup two-factor authentication for a user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Generate a TOTP setup for the authenticated user",
        responses={
            200: OpenApiResponse(description="Returns setup details including QR code"),
            400: OpenApiResponse(description="User already has 2FA enabled"),
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Check if user already has 2FA set up
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return Response(
                {'error': _('Two-factor authentication is already enabled')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate a new TOTP device
        device, created = TOTPDevice.objects.get_or_create(
            user=user,
            confirmed=False,
            defaults={'name': f"{user.email}'s device"}
        )
        
        if not created:
            # Regenerate key for existing unconfirmed device
            device.key = TOTPDevice.random_key()
            device.save()
        
        # Format key as base32 for QR code
        key = device.bin_key
        totp = pyotp.TOTP(base64.b32encode(key).decode('utf-8'))
        
        # Generate QR code
        provision_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Dealopia"
        )
        
        img = qrcode.make(provision_uri)
        buffer = io.BytesIO()
        img.save(buffer)
        qr_code = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return Response({
            'qr_code': f"data:image/png;base64,{qr_code}",
            'secret': base64.b32encode(key).decode('utf-8'),
            'instructions': _('Scan this QR code with your authenticator app, or enter the secret key manually.')
        })
    
    @extend_schema(
        description="Confirm and enable 2FA setup with a verification code",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'description': 'TOTP token (6-digit code)'},
                },
                'required': ['token']
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully enabled"),
            400: OpenApiResponse(description="Invalid verification code"),
            404: OpenApiResponse(description="No pending 2FA setup found"),
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': _('Verification code is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            device = TOTPDevice.objects.get(user=user, confirmed=False)
            
            if device.verify_token(token):
                # Mark device as confirmed
                device.confirmed = True
                device.save()
                
                return Response({
                    'success': True,
                    'message': _('Two-factor authentication has been enabled successfully')
                })
            else:
                return Response(
                    {'error': _('Invalid verification code')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except TOTPDevice.DoesNotExist:
            return Response(
                {'error': _('No pending two-factor setup found')},
                status=status.HTTP_404_NOT_FOUND
            )

class TwoFactorDisableView(APIView):
    """
    Disable two-factor authentication for a user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Disable 2FA for the authenticated user (requires password confirmation)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'password': {'type': 'string', 'description': 'User password for confirmation'},
                },
                'required': ['password']
            }
        },
        responses={
            200: OpenApiResponse(description="2FA successfully disabled"),
            400: OpenApiResponse(description="Invalid password or missing confirmation"),
            404: OpenApiResponse(description="User has no 2FA enabled"),
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': _('Password confirmation is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify password
        if not user.check_password(password):
            return Response(
                {'error': _('Invalid password')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete all TOTP devices for user
        devices = TOTPDevice.objects.filter(user=user)
        if not devices.exists():
            return Response(
                {'error': _('Two-factor authentication is not enabled for this user')},
                status=status.HTTP_404_NOT_FOUND
            )
            
        devices.delete()
        
        return Response({
            'success': True,
            'message': _('Two-factor authentication has been disabled successfully')
        })

class SocialAuthCallbackView(APIView):
    """
    Handle social authentication callbacks and return JWT tokens
    """
    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        # This is a simplified example - in practice you would:
        # 1. Get the auth code from the request
        # 2. Exchange it for an access token with the provider
        # 3. Get user info from the provider
        # 4. Create or get the user in your database
        
        # For demo purposes, we'll assume we already have the user
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': _('Authentication failed')},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Instead of returning a Response, redirect to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access={str(refresh.access_token)}&refresh={str(refresh)}"
        
        return redirect(redirect_url)

class SessionInfoView(APIView):
    """
    Get information about the current authenticated session
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        description="Get information about the current authenticated session",
        responses={
            200: OpenApiResponse(description="Returns session details including 2FA status"),
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Check if user has 2FA enabled
        has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        
        # Get the expiry time of the current token
        # This would typically be calculated from the JWT payload
        # For simplicity, we'll just return a fixed value
        token_expires_in = 1800  # 30 minutes in seconds
        
        return Response({
            'user_id': str(user.id),
            'email': user.email,
            'has_2fa_enabled': has_2fa,
            'token_expires_in': token_expires_in,
            'last_login': user.last_login,
        })

class TokenRefreshRateLimitedView(APIView):
    """
    Custom token refresh view with rate limiting to prevent abuse
    """
    permission_classes = []
    throttle_scope = 'token_refresh'
    
    @extend_schema(
        description="Refresh an expired access token",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'Refresh token'},
                },
                'required': ['refresh']
            }
        },
        responses={
            200: OpenApiResponse(description="Returns new access token"),
            401: OpenApiResponse(description="Invalid or expired refresh token"),
        }
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': _('Refresh token is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            refresh = RefreshToken(refresh_token)
            
            # Get user from token payload
            user_id = refresh.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Check if user account is still active
            if not user.is_active:
                return Response(
                    {'error': _('User account is disabled')},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            # Generate new access token
            return Response({
                'access': str(refresh.access_token),
            })
                
        except (TokenError, User.DoesNotExist) as e:
            return Response(
                {'error': _('Invalid or expired refresh token')},
                status=status.HTTP_401_UNAUTHORIZED
            )