"""
GreenGrid Facilities Selectors (Read Queries with Tenancy Scoping).
"""

from django.http import Http404
from facilities.models import Facility, Building, Meter, DataSource
from core.scoping import get_user_facility_ids

def list_facilities_for_user(user, facility_type=None, city=None):
    qs = Facility.objects.all().order_by('name')
    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(id__in=facility_ids)

    if facility_type:
        qs = qs.filter(facility_type=facility_type)
    if city:
        qs = qs.filter(city__iexact=city)
    return qs

def get_facility_for_user(facility_id: int, user) -> Facility:
    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None and int(facility_id) not in facility_ids:
        raise Http404(f"Facility with ID {facility_id} does not exist.")
    try:
        return Facility.objects.get(id=facility_id)
    except Facility.DoesNotExist:
        raise Http404(f"Facility with ID {facility_id} does not exist.")

def list_buildings_for_facility(facility: Facility):
    return Building.objects.filter(facility=facility).order_by('name')

def list_meters_for_facility(facility: Facility, energy_source=None, load_category=None):
    qs = Meter.objects.filter(facility=facility).select_related('building').order_by('name')
    if energy_source:
        qs = qs.filter(energy_source=energy_source)
    if load_category:
        qs = qs.filter(load_category=load_category)
    return qs

def list_datasources_for_facility(facility: Facility):
    return DataSource.objects.filter(facility=facility).order_by('-created_at')
