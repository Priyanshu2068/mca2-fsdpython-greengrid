"""
GreenGrid Billing Selectors (Read Queries).
"""

from billing.models import UtilityProvider, TariffStructure, UtilityBill, BillReconciliation
from core.scoping import get_user_facility_ids

def list_utility_providers():
    return UtilityProvider.objects.all().order_by('name')

def list_tariffs(provider_id=None):
    qs = TariffStructure.objects.select_related('provider').all().order_by('tariff_code')
    if provider_id:
        qs = qs.filter(provider_id=provider_id)
    return qs

def list_utility_bills(user, facility_id=None, year=None):
    qs = UtilityBill.objects.select_related('facility', 'tariff', 'tariff__provider').all().order_by('-billing_cycle_start')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(facility_id=facility_id)
    if year:
        qs = qs.filter(billing_cycle_start__year=year)
    return qs

def list_reconciliations(user, bill_id=None, facility_id=None):
    qs = BillReconciliation.objects.select_related('bill', 'bill__facility', 'bill__tariff').all().order_by('-reconciled_at')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(bill__facility_id__in=facility_ids)

    if bill_id:
        qs = qs.filter(bill_id=bill_id)
    if facility_id:
        qs = qs.filter(bill__facility_id=facility_id)
    return qs
