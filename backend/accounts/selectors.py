"""
GreenGrid Accounts Selectors (Read Queries & Filters).
"""

from accounts.models import CustomUser, AuditLog

def get_user_by_id(user_id):
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return None

def list_users(role=None, is_active=None, search=None):
    qs = CustomUser.objects.all().order_by('-date_joined')
    if role:
        qs = qs.filter(role=role)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if search:
        qs = qs.filter(email__icontains=search)
    return qs

def list_audit_logs(user_id=None, action=None, resource_type=None):
    qs = AuditLog.objects.select_related('user').all().order_by('-timestamp')
    if user_id:
        qs = qs.filter(user_id=user_id)
    if action:
        qs = qs.filter(action=action)
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    return qs
