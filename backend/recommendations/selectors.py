"""
GreenGrid Recommendations Selectors.
Scoping, Aggregations & Query Filters.
"""

from django.db.models import Sum, Count, Q
from decimal import Decimal
from recommendations.models import ECMRule, Recommendation
from core.scoping import get_user_facility_ids
from facilities.selectors import get_facility_for_user
from django.http import Http404

def list_ecm_rules():
    return ECMRule.objects.filter(is_active=True).order_by('rule_code')

def get_recommendations_for_user(user, facility_id=None, status=None, category=None):
    qs = Recommendation.objects.select_related('rule', 'facility', 'meter').all()

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        # Validate tenancy
        get_facility_for_user(facility_id=facility_id, user=user)
        qs = qs.filter(facility_id=facility_id)

    if status:
        qs = qs.filter(status=status)

    if category:
        qs = qs.filter(rule__category=category)

    return qs.order_by('-estimated_annual_savings_inr')

def get_recommendation_by_id(user, recommendation_id: int) -> Recommendation:
    try:
        recom = Recommendation.objects.select_related('rule', 'facility', 'meter').get(id=recommendation_id)
    except Recommendation.DoesNotExist:
        raise Http404(f"Recommendation with ID {recommendation_id} not found.")

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None and recom.facility_id not in facility_ids:
        raise Http404(f"Recommendation with ID {recommendation_id} not found.")

    return recom

def get_recommendations_summary(user, facility_id=None) -> dict:
    qs = get_recommendations_for_user(user, facility_id=facility_id)

    total_count = qs.count()
    active_count = qs.filter(status='active').count()
    accepted_count = qs.filter(status='accepted').count()
    dismissed_count = qs.filter(status='dismissed').count()

    total_potential_savings = qs.aggregate(s=Sum('estimated_annual_savings_inr'))['s'] or Decimal('0.00')
    accepted_annual_savings = qs.filter(status='accepted').aggregate(s=Sum('estimated_annual_savings_inr'))['s'] or Decimal('0.00')
    total_potential_kwh = qs.aggregate(s=Sum('estimated_annual_kwh_savings'))['s'] or Decimal('0.0000')
    accepted_annual_kwh = qs.filter(status='accepted').aggregate(s=Sum('estimated_annual_kwh_savings'))['s'] or Decimal('0.0000')

    return {
        'total_recommendations': total_count,
        'active_count': active_count,
        'accepted_count': accepted_count,
        'dismissed_count': dismissed_count,
        'total_potential_savings_inr': total_potential_savings,
        'accepted_annual_savings_inr': accepted_annual_savings,
        'total_potential_kwh_savings': total_potential_kwh,
        'accepted_annual_kwh_savings': accepted_annual_kwh,
    }
