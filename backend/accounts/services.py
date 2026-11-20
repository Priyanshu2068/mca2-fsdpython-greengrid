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


# ---------------------------------------------------------------------------
# User onboarding with facility access (admins and field engineers)
# ---------------------------------------------------------------------------

# Which roles each kind of creator may provision.
CREATABLE_ROLES = {
    'admin': ('customer', 'field_engineer'),
    'field_engineer': ('customer',),
}


def _creator_kind(actor):
    if getattr(actor, 'is_superuser', False) or getattr(actor, 'role', None) == 'admin':
        return 'admin'
    return getattr(actor, 'role', None)


def _validated_facility_ids(actor, facility_ids):
    """
    Returns the de-duplicated facility ids the actor is allowed to grant.
    Admins can grant any existing facility (unknown ids are a validation error).
    Other roles can only grant facilities they are assigned to (404 otherwise,
    so out-of-scope facilities are never revealed).
    """
    from django.http import Http404
    from rest_framework.exceptions import ValidationError as DRFValidationError
    from core.scoping import get_user_facility_ids
    from facilities.models import Facility

    ids = sorted({int(i) for i in (facility_ids or [])})
    scope = get_user_facility_ids(actor)
    if scope is None:
        existing = set(Facility.objects.filter(id__in=ids).values_list('id', flat=True))
        missing = [i for i in ids if i not in existing]
        if missing:
            raise DRFValidationError({'facility_ids': [f'Unknown facility id(s): {missing}.']})
        return ids
    if any(i not in scope for i in ids):
        raise Http404('Facility not found.')
    return ids


@transaction.atomic
def create_user_with_access(actor, email, password, role, first_name='', last_name='', phone='',
                            facility_ids=None, ip_address=None):
    """
    Creates a user and grants facility access in one step.
    - admin may create customers and field engineers (facilities optional);
    - field engineer may create customers for their own facilities (at least one required).
    """
    from rest_framework.exceptions import PermissionDenied
    from rest_framework.exceptions import ValidationError as DRFValidationError
    from facilities.models import UserFacilityAssignment

    kind = _creator_kind(actor)
    allowed = CREATABLE_ROLES.get(kind, ())
    if role not in allowed:
        raise PermissionDenied(
            'You can create these roles: ' + (', '.join(allowed) if allowed else 'none') + '.')

    ids = _validated_facility_ids(actor, facility_ids)
    if kind != 'admin' and not ids:
        raise DRFValidationError({'facility_ids': ['Select at least one facility for the new user.']})

    user = create_user_by_admin(
        admin_user=actor, email=email, password=password, role=role,
        first_name=first_name, last_name=last_name, phone=phone, ip_address=ip_address,
    )
    for fid in ids:
        UserFacilityAssignment.objects.get_or_create(user=user, facility_id=fid)
    record_audit_log(
        user=actor, action='GRANT_FACILITY_ACCESS', resource_type='CustomUser', resource_id=user.id,
        ip_address=ip_address, details={'email': user.email, 'facility_ids': ids},
    )
    return user


@transaction.atomic
def set_user_facilities(actor, target, facility_ids, ip_address=None):
    """
    Replaces the facility access of a user within the actor's own scope.
    Access the actor does not control (other facilities) is left untouched.
    Admins may manage customers and field engineers; field engineers only customers.
    """
    from rest_framework.exceptions import PermissionDenied
    from core.scoping import get_user_facility_ids
    from facilities.models import UserFacilityAssignment

    kind = _creator_kind(actor)
    if target.role not in CREATABLE_ROLES.get(kind, ()) or target.is_superuser:
        raise PermissionDenied('You cannot change facility access for this user.')

    requested = set(_validated_facility_ids(actor, facility_ids))
    current = set(UserFacilityAssignment.objects.filter(user=target).values_list('facility_id', flat=True))
    scope = get_user_facility_ids(actor)
    managed = current | requested if scope is None else set(scope)

    final = (current - managed) | (requested & managed)
    if kind != 'admin' and not (final & set(scope or [])):
        from rest_framework.exceptions import ValidationError as DRFValidationError
        raise DRFValidationError({'facility_ids': ['Keep at least one facility for this user.']})

    UserFacilityAssignment.objects.filter(user=target, facility_id__in=current - final).delete()
    for fid in final - current:
        UserFacilityAssignment.objects.get_or_create(user=target, facility_id=fid)

    record_audit_log(
        user=actor, action='UPDATE_FACILITY_ACCESS', resource_type='CustomUser', resource_id=target.id,
        ip_address=ip_address,
        details={'email': target.email, 'added': sorted(final - current), 'removed': sorted(current - final)},
    )
    return target
