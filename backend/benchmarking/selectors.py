"""
GreenGrid Benchmarking Selectors.
"""

from benchmarking.models import BuildingBenchmark, FacilityBenchmarkScore
from core.scoping import get_user_facility_ids

def list_building_benchmarks():
    return BuildingBenchmark.objects.all().order_by('facility_type')

def get_facility_benchmark_scores(user, facility_id=None, year=None):
    qs = FacilityBenchmarkScore.objects.select_related('facility').all().order_by('-year', 'calculated_eui_kwh_sqm_year')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(facility_id=facility_id)
    if year:
        qs = qs.filter(year=year)
    return qs

def get_facility_rankings(user, facility_type=None, year=None):
    qs = FacilityBenchmarkScore.objects.select_related('facility').all().order_by('calculated_eui_kwh_sqm_year')
    if facility_type:
        qs = qs.filter(facility__facility_type=facility_type)
    if year:
        qs = qs.filter(year=year)
    return qs

