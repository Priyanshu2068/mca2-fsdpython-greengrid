"""
GreenGrid Role-Based Access Control (RBAC) Permissions.
"""

from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    """
    Enforces per-action role-based authorization.
    Views define a dictionary:
    role_permissions = {
        'admin': ['list', 'retrieve', 'create', 'update', 'destroy'],
        'customer': ['list', 'retrieve'],
        'field_engineer': ['list', 'retrieve', 'create']
    }
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers bypass checks
        if getattr(request.user, 'is_superuser', False):
            return True

        user_role = getattr(request.user, 'role', None)
        if not user_role:
            return False

        role_permissions = getattr(view, 'role_permissions', None)
        if not role_permissions:
            # If view doesn't define explicit role_permissions, default to allowing authenticated users
            return True

        allowed_actions = role_permissions.get(user_role, [])
        action = getattr(view, 'action', request.method.lower())
        return action in allowed_actions

class IsAdminUser(BasePermission):
    """Allows access only to users with role 'admin' or superusers."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (getattr(request.user, 'role', None) == 'admin' or request.user.is_superuser)
        )

class IsCustomerUser(BasePermission):
    """Allows access only to users with role 'customer'."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'customer'
        )

class IsFieldEngineerUser(BasePermission):
    """Allows access only to users with role 'field_engineer'."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'field_engineer'
        )
