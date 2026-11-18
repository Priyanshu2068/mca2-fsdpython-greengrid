"""
GreenGrid Accounts Views (Session Auth, User Management, Audit Logs).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema

from accounts.models import CustomUser, AuditLog
from accounts.serializers import (
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserCreateSerializer,
    AuditLogSerializer,
)
from accounts.services import (
    record_audit_log,
    create_user_by_admin,
    change_user_password,
)
from accounts.selectors import list_users, list_audit_logs
from core.permissions import IsAdminUser

class CSRFTokenView(APIView):
    """
    Sets the csrftoken HTTP cookie and returns token string for SPA session initiation.
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return Response({'csrfToken': token}, status=status.HTTP_200_OK)

class LoginView(APIView):
    """
    Authenticates email and password, establishing a Django session cookie.
    """
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: UserProfileSerializer})
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {
                    'error': {
                        'status': status.HTTP_401_UNAUTHORIZED,
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid email or password provided.',
                        'details': {'email': ['Authentication failed with provided credentials.']}
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {
                    'error': {
                        'status': status.HTTP_403_FORBIDDEN,
                        'code': 'ACCOUNT_INACTIVE',
                        'message': 'This account has been disabled.',
                        'details': {'account': ['Please contact the administrator.']}
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        login(request, user)
        record_audit_log(
            user=user,
            action='LOGIN_SUCCESS',
            resource_type='Session',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    Terminates the current authenticated session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        record_audit_log(
            user=request.user,
            action='LOGOUT',
            resource_type='Session',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        logout(request)
        return Response({'status': 'logged_out', 'message': 'Session successfully terminated.'}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    """
    Retrieves currently authenticated user's profile and assigned facilities.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request, *args, **kwargs):
        return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """
    Changes current user password and maintains active session.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = change_user_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password'],
            ip_address=request.META.get('REMOTE_ADDR')
        )
        update_session_auth_hash(request, user)
        return Response({'status': 'password_changed', 'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)

class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Administrator API for provisioning and managing system users.
    """
    permission_classes = [IsAdminUser]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        role = self.request.query_params.get('role')
        search = self.request.query_params.get('search')
        return list_users(role=role, search=search)

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = create_user_by_admin(
            admin_user=request.user,
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            role=serializer.validated_data['role'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            phone=serializer.validated_data.get('phone', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)

class AuditLogListView(APIView):
    """
    Administrator view of system security and operational audit logs.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: AuditLogSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        action = request.query_params.get('action')
        resource_type = request.query_params.get('resource_type')
        logs = list_audit_logs(action=action, resource_type=resource_type)
        return Response(AuditLogSerializer(logs[:200], many=True).data, status=status.HTTP_200_OK)
