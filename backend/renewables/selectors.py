"""
GreenGrid Renewables Selectors.
Read queries with facility scoping for solar assets, generation, grid events, and carbon factors.
"""

from django.http import Http404
from core.scoping import get_user_facility_ids
from facilities.selectors import get_facility_for_user
from renewables.models import (
    SolarAsset,
    SolarGenerationReading,
    GridEvent,
    CarbonEmissionFactor,
)

def list_solar_assets(user, facility_id=None):
    qs = SolarAsset.objects.select_related('facility').filter(is_active=True)

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        get_facility_for_user(facility_id=facility_id, user=user)
        qs = qs.filter(facility_id=facility_id)

    return qs.order_by('facility__name', 'array_identifier')

def get_solar_generation_readings(user, asset_id=None, facility_id=None, start_date=None, end_date=None):
    qs = SolarGenerationReading.objects.select_related('asset', 'asset__facility').all()

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(asset__facility_id__in=facility_ids)

    if facility_id:
        get_facility_for_user(facility_id=facility_id, user=user)
        qs = qs.filter(asset__facility_id=facility_id)

    if asset_id:
        qs = qs.filter(asset_id=asset_id)

    if start_date:
        qs = qs.filter(timestamp__date__gte=start_date)
    if end_date:
        qs = qs.filter(timestamp__date__lte=end_date)

    return qs.order_by('-timestamp')

def get_grid_events(user, facility_id=None, event_type=None):
    qs = GridEvent.objects.select_related('facility').all()

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        get_facility_for_user(facility_id=facility_id, user=user)
        qs = qs.filter(facility_id=facility_id)

    if event_type:
        qs = qs.filter(event_type=event_type)

    return qs.order_by('-start_time')

def get_carbon_emission_factors():
    return CarbonEmissionFactor.objects.all().order_by('energy_source')

