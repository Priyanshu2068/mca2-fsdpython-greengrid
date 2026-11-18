"""
GreenGrid Accounts Services (Write Logic & Domain Mutations).
"""

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.db import transaction
from accounts.models import CustomUser, AuditLog

def record_audit_log(user, action, resource_type, resource_id='', ip_address=None, user_agent='', details=None):
    """
    Persists an audit entry tracking administrative or security events.
    """
    return AuditLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address,
        user_agent=user_agent or '',
        details=details or {}
    )

@transaction.atomic
def create_user_by_admin(admin_user, email, password, role, first_name='', last_name='', phone='', ip_address=None):
    """
    Provisions a new user in the system with role and records audit trace.
    """
    email_clean = email.strip().lower()
    if CustomUser.objects.filter(email=email_clean).exists():
        raise ValidationError({'email': ['A user with this email address already exists.']})

    user = CustomUser.objects.create_user(
        email=email_clean,
        password=password,
        role=role,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )

    record_audit_log(
        user=admin_user,
        action='CREATE_USER',
        resource_type='CustomUser',
        resource_id=user.id,
        ip_address=ip_address,
        details={'email': user.email, 'role': user.role}
    )
    return user

def change_user_password(user, old_password, new_password, ip_address=None):
    """
    Validates old password and sets new password.
    """
    if not user.check_password(old_password):
        raise ValidationError({'old_password': ['Current password does not match.']})

    if len(new_password) < 8:
        raise ValidationError({'new_password': ['Password must be at least 8 characters long.']})

    user.set_password(new_password)
    user.save(update_fields=['password'])

    record_audit_log(
        user=user,
        action='CHANGE_PASSWORD',
        resource_type='CustomUser',
        resource_id=user.id,
        ip_address=ip_address
    )
    return user
