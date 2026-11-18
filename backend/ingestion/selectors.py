"""
GreenGrid Ingestion Selectors (Read Queries).
"""

from ingestion.models import RawReading, BatchLog
from core.scoping import get_user_facility_ids

def list_raw_readings(user, facility_id=None, meter_id=None, meter_identifier=None, start_time=None, end_time=None):
    qs = RawReading.objects.select_related('meter', 'meter__facility').all().order_by('-timestamp')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(meter__facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(meter__facility_id=facility_id)
    if meter_id:
        qs = qs.filter(meter_id=meter_id)
    if meter_identifier:
        qs = qs.filter(meter__meter_identifier=meter_identifier)
    if start_time:
        qs = qs.filter(timestamp__gte=start_time)
    if end_time:
        qs = qs.filter(timestamp__lte=end_time)

    return qs

def list_batches(user, source_type=None):
    qs = BatchLog.objects.select_related('datasource', 'uploaded_by').all().order_by('-created_at')
    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(datasource__facility_id__in=facility_ids)
    if source_type:
        qs = qs.filter(source_type=source_type)
    return qs
