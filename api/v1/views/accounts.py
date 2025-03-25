from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import IsOwnerOrReadOnly
from api.v1.serializers.accounts import (
    EmailChangeRequestSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from apps.accounts.models import User

class UserViewSet(viewsets.ModelViewSet):
    """Enhanced API endpoint for user management with improved security and features"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'email'
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_staff:
            return super().get_queryset()
        return User.objects.filter(id=self.request.user.id)
    
    def get_permissions(self):
        """Set permission classes dynamically based on action"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
            
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        serializer_map = {
            'create': UserCreateSerializer,
            'update_profile': ProfileUpdateSerializer,
            'change_password': PasswordChangeSerializer,
            'change_email': EmailChangeRequestSerializer,
        }
        return serializer_map.get(self.action, UserSerializer)
    
    @extend_schema(
        description="Get the current authenticated user's profile",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current authenticated user profile"""
        user = request.user
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @extend_schema(
        description="Update the current user's profile",
        request=ProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['patch'])
    def profile(self, request):
        """Update current user profile without changing email/password"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserSerializer(user).data)
    
    @extend_schema(
        description="Change the current user's password",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid data or password"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password with current password verification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {"detail": _("Password changed successfully.")},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="Request email change (sends verification email)",
        request=EmailChangeRequestSerializer,
        responses={
            200: OpenApiResponse(description="Verification email sent"),
            400: OpenApiResponse(description="Invalid data or email"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['post'])
    def change_email(self, request):
        """Request email change with verification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_email = serializer.validated_data['new_email']
        user.create_email_change_request(new_email)
        
        return Response(
            {"detail": _("Verification email sent to {email}. Please check your inbox.").format(email=new_email)},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="Verify email change with token",
        parameters=[
            OpenApiParameter(name="token", location=OpenApiParameter.QUERY, 
                            description="Verification token", required=True),
        ],
        responses={
            200: OpenApiResponse(description="Email changed successfully"),
            400: OpenApiResponse(description="Invalid or expired token"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['get'])
    def verify_email_change(self, request):
        """Verify and complete email change process"""
        token = request.query_params.get('token')
        if not token:
            return Response(
                {"detail": _("Verification token is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            request.user.confirm_email_change(token)
            return Response(
                {"detail": _("Email address has been changed successfully.")},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        description="Get user's notification settings",
        responses={
            200: OpenApiResponse(description="Notification settings retrieved"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['get'])
    def notifications(self, request):
        """Get user notification preferences"""
        return Response(request.user.notification_preferences or {})
    
    @extend_schema(
        description="Update user's notification settings",
        responses={
            200: OpenApiResponse(description="Notification settings updated"),
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Not authenticated")
        }
    )
    @action(detail=False, methods=['patch'])
    def update_notifications(self, request):
        """Update user notification preferences"""
        user = request.user
        preferences = user.notification_preferences or {}
        preferences.update(request.data)
        
        user.notification_preferences = preferences
        user.save(update_fields=['notification_preferences'])
        
        return Response(preferences)
    
    @extend_schema(
        description="Deactivate user account (does not delete)",
        responses={
            200: OpenApiResponse(description="Account deactivated"),
            401: OpenApiResponse(description="Not authenticated"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=False, methods=['post'])
    def deactivate(self, request):
        """Deactivate user account (soft delete)"""
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        return Response(
            {"detail": _("Your account has been deactivated.")},
            status=status.HTTP_200_OK
        )
