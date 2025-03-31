import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import (
    OpenApiParameter, 
    OpenApiResponse,
    extend_schema
)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissions import IsOwnerOrReadOnly
from api.v1.serializers.accounts import (
    EmailChangeRequestSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    UserCreateSerializer, 
    UserSerializer
)
from apps.accounts.models import User


class UserViewSet(viewsets.ModelViewSet):
    """User management API with security features and granular permissions"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "email"
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return User.objects.filter(id=self.request.user.id)

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        serializer_map = {
            "create": UserCreateSerializer,
            "update_profile": ProfileUpdateSerializer,
            "change_password": PasswordChangeSerializer,
            "change_email": EmailChangeRequestSerializer,
        }
        return serializer_map.get(self.action, UserSerializer)

    def _update_user_response(self, user, data=None, partial=True):
        """Helper method for updating user and returning response"""
        serializer = self.get_serializer(user, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)

    def _create_detail_response(self, message, status_code=status.HTTP_200_OK):
        """Helper method to create consistent detail responses"""
        return Response({"detail": _(message)}, status=status_code)

    @extend_schema(
        description="Get current authenticated user's profile",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["get"])
    def me(self, request):
        user = request.user
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        description="Update the current user's profile",
        request=ProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["patch"])
    def profile(self, request):
        return self._update_user_response(request.user, request.data)

    @extend_schema(
        description="Change the current user's password",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid data or password"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self._create_detail_response("Password changed successfully.")

    @extend_schema(
        description="Request email change (sends verification email)",
        request=EmailChangeRequestSerializer,
        responses={
            200: OpenApiResponse(description="Verification email sent"),
            400: OpenApiResponse(description="Invalid data or email"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["post"])
    def change_email(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data["new_email"]
        user.create_email_change_request(new_email)

        return self._create_detail_response(
            "Verification email sent to {email}. Please check your inbox.".format(email=new_email)
        )

    @extend_schema(
        description="Verify email change with token",
        parameters=[
            OpenApiParameter(
                name="token",
                location=OpenApiParameter.QUERY,
                description="Verification token",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Email changed successfully"),
            400: OpenApiResponse(description="Invalid or expired token"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["get"])
    def verify_email_change(self, request):
        token = request.query_params.get("token")
        if not token:
            return self._create_detail_response(
                "Verification token is required.", 
                status.HTTP_400_BAD_REQUEST
            )

        try:
            request.user.confirm_email_change(token)
            return self._create_detail_response("Email address has been changed successfully.")
        except Exception as e:
            return self._create_detail_response(str(e), status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Get user's notification settings",
        responses={
            200: OpenApiResponse(description="Notification settings retrieved"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["get"])
    def notifications(self, request):
        return Response(request.user.notification_preferences or {})

    @extend_schema(
        description="Update user's notification settings",
        responses={
            200: OpenApiResponse(description="Notification settings updated"),
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    @action(detail=False, methods=["patch"])
    def update_notifications(self, request):
        user = request.user
        preferences = user.notification_preferences or {}
        preferences.update(request.data)

        user.notification_preferences = preferences
        user.save(update_fields=["notification_preferences"])

        return Response(preferences)

    @extend_schema(
        description="Deactivate user account (does not delete)",
        responses={
            200: OpenApiResponse(description="Account deactivated"),
            401: OpenApiResponse(description="Not authenticated"),
            403: OpenApiResponse(description="Permission denied"),
        },
    )
    @action(detail=False, methods=["post"])
    def deactivate(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        return self._create_detail_response("Your account has been deactivated.")
