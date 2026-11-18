"""
GreenGrid Analytics Selectors (Read Queries with Tenancy Scoping).
"""

from analytics.models import HourlyRollup, DailyRollup, AnomalyAlert
from core.scoping import get_user_facility_ids

def get_hourly_rollups(user, facility_id=None, meter_id=None, start_time=None, end_time=None):
    qs = HourlyRollup.objects.select_related('meter', 'meter__facility').all().order_by('-bucket_start')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(meter__facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(meter__facility_id=facility_id)
    if meter_id:
        qs = qs.filter(meter_id=meter_id)
    if start_time:
        qs = qs.filter(bucket_start__gte=start_time)
    if end_time:
        qs = qs.filter(bucket_start__lte=end_time)

    return qs

def get_daily_rollups(user, facility_id=None, meter_id=None, start_date=None, end_date=None):
    qs = DailyRollup.objects.select_related('meter', 'meter__facility').all().order_by('-rollup_date')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(meter__facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(meter__facility_id=facility_id)
    if meter_id:
        qs = qs.filter(meter_id=meter_id)
    if start_date:
        qs = qs.filter(rollup_date__gte=start_date)
    if end_date:
        qs = qs.filter(rollup_date__lte=end_date)

    return qs

def list_anomaly_alerts(user, facility_id=None, status=None, severity=None, anomaly_type=None):
    qs = AnomalyAlert.objects.select_related('facility', 'meter').all().order_by('-detected_at')

    facility_ids = get_user_facility_ids(user)
    if facility_ids is not None:
        qs = qs.filter(facility_id__in=facility_ids)

    if facility_id:
        qs = qs.filter(facility_id=facility_id)
    if status:
        qs = qs.filter(status=status)
    if severity:
        qs = qs.filter(severity=severity)
    if anomaly_type:
        qs = qs.filter(anomaly_type=anomaly_type)

    return qs

