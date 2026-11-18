"""
GreenGrid Multi-Tenant Facility Tenancy Scoping Engine.
Ensures that out-of-scope objects return HTTP 404 (preventing enumeration attacks).
"""

from django.http import Http404
from rest_framework.exceptions import NotFound

def get_user_facility_ids(user):
    """
    Returns a list of facility IDs accessible to the given user.
    Admins have global access (returns None).
    """
    if not user or not user.is_authenticated:
        return []
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'admin':
        return None # Global scope

    # Look up assigned facility IDs through the user's assignments
    if hasattr(user, 'facility_assignments'):
        return list(user.facility_assignments.values_list('facility_id', flat=True))
    if hasattr(user, 'assigned_facilities'):
        return list(user.assigned_facilities.values_list('id', flat=True))
    return []

class FacilityScopedQuerySetMixin:
    """
    QuerySet mixin for ViewSets and APIViews that filters by user's assigned facilities.
    """
    facility_lookup_field = 'facility_id'

    def filter_by_facility_scope(self, queryset):
        user = self.request.user
        facility_ids = get_user_facility_ids(user)
        if facility_ids is None:
            return queryset # Admin: unconstrained

        lookup = {f"{self.facility_lookup_field}__in": facility_ids}
        return queryset.filter(**lookup)

    def check_facility_scope(self, facility_id):
        """
        Validates whether the user has access to a specific facility_id.
        Raises Http404 if inaccessible to prevent resource discovery.
        """
        user = self.request.user
        facility_ids = get_user_facility_ids(user)
        if facility_ids is None:
            return True # Admin
        if int(facility_id) not in facility_ids:
            raise Http404(f"Facility with ID {facility_id} does not exist.")
        return True
