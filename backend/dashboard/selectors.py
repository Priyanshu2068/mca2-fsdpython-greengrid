"""
GreenGrid Dashboard Selectors (High-Speed Pre-Aggregated Lookups < 1 Second).
Reads EXCLUSIVELY from HourlyRollup and DailyRollup tables. Zero scans on raw_readings.
"""

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Max
from facilities.selectors import get_facility_for_user
from analytics.models import HourlyRollup, DailyRollup, AnomalyAlert

def get_facility_kpi_summary(facility_id: int, user) -> dict:
    """
    Computes real-time executive KPIs for a facility from rollups under 1s.
    """
    facility = get_facility_for_user(facility_id, user)
    now_local = timezone.localtime(timezone.now())
    today = now_local.date()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)

    meter_ids = list(facility.meters.filter(is_active=True).values_list('id', flat=True))
    incomer_meter_ids = list(
        facility.meters.filter(is_active=True, load_category='main_incomer', energy_source='grid')
        .values_list('id', flat=True)
    ) or meter_ids

    # 1. Today's consumption (sum of hourly rollups for today)
    today_kwh = (
        HourlyRollup.objects.filter(meter_id__in=incomer_meter_ids, bucket_start__date=today)
        .aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0.0000')
    )

    # 2. Yesterday's consumption (from DailyRollup)
    yesterday_kwh = (
        DailyRollup.objects.filter(meter_id__in=incomer_meter_ids, rollup_date=yesterday)
        .aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0.0000')
    )

    # Percentage change
    if yesterday_kwh > Decimal('0.0000'):
        change_pct = round(((today_kwh - yesterday_kwh) / yesterday_kwh) * Decimal('100.0'), 2)
    else:
        change_pct = Decimal('0.00')

    # 3. Month to Date (MTD) consumption
    mtd_kwh = (
        DailyRollup.objects.filter(meter_id__in=incomer_meter_ids, rollup_date__gte=month_start, rollup_date__lt=today)
        .aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0.0000')
    ) + today_kwh

    # 4. Current Peak Demand (today)
    peak_demand_kw = (
        HourlyRollup.objects.filter(meter_id__in=incomer_meter_ids, bucket_start__date=today)
        .aggregate(max_kw=Max('peak_demand_kw'))['max_kw'] or Decimal('0.0000')
    )

    # Sanctioned demand utilization
    sanctioned_kva = facility.sanctioned_demand_kva or Decimal('500.00')
    demand_utilization_pct = round((peak_demand_kw / sanctioned_kva) * Decimal('100.0'), 2)

    # Newest hour that has data (lets the UI say "no readings yet today" instead of showing a bare 0)
    latest_bucket = HourlyRollup.objects.filter(meter_id__in=incomer_meter_ids).aggregate(m=Max('bucket_start'))['m']

    # 5. Active Anomaly Alerts count
    active_anomalies_count = AnomalyAlert.objects.filter(facility=facility, status='open').count()

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'as_of': now_local.isoformat(),
        'latest_data_at': timezone.localtime(latest_bucket).isoformat() if latest_bucket else None,
        'metrics': {
            'today_consumption_kwh': today_kwh,
            'yesterday_same_time_kwh': yesterday_kwh,
            'change_percentage': change_pct,
            'month_to_date_kwh': mtd_kwh,
            'current_peak_demand_kw': peak_demand_kw,
            'sanctioned_demand_kva': sanctioned_kva,
            'demand_utilization_pct': demand_utilization_pct,
            'active_anomalies_count': active_anomalies_count,
        }
    }

def get_facility_trends(facility_id: int, user, range_type='24h') -> dict:
    facility = get_facility_for_user(facility_id, user)
    incomer_meter_ids = list(
        facility.meters.filter(is_active=True, load_category='main_incomer', energy_source='grid')
        .values_list('id', flat=True)
    ) or list(facility.meters.filter(is_active=True).values_list('id', flat=True))

    data_points = []
    if range_type == '24h':
        now = timezone.now()
        cutoff = now - timedelta(hours=24)
        rollups = (
            HourlyRollup.objects.filter(meter_id__in=incomer_meter_ids, bucket_start__gte=cutoff)
            .values('bucket_start')
            .annotate(total_kwh=Sum('total_energy_kwh'), peak_kw=Max('peak_demand_kw'))
            .order_by('bucket_start')
        )
        for r in rollups:
            data_points.append({
                'timestamp': r['bucket_start'].isoformat(),
                'energy_kwh': r['total_kwh'] or Decimal('0.0000'),
                'peak_demand_kw': r['peak_kw'] or Decimal('0.0000')
            })
    else: # 30d
        cutoff = timezone.now().date() - timedelta(days=30)
        daily_rollups = (
            DailyRollup.objects.filter(meter_id__in=incomer_meter_ids, rollup_date__gte=cutoff)
            .values('rollup_date')
            .annotate(total_kwh=Sum('total_energy_kwh'), peak_kw=Max('peak_demand_kw'))
            .order_by('rollup_date')
        )
        for r in daily_rollups:
            data_points.append({
                'date': r['rollup_date'].isoformat(),
                'energy_kwh': r['total_kwh'] or Decimal('0.0000'),
                'peak_demand_kw': r['peak_kw'] or Decimal('0.0000')
            })

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'range': range_type,
        'points': data_points
    }

def get_facility_energy_mix(facility_id: int, user) -> dict:
    facility = get_facility_for_user(facility_id, user)
    cutoff = timezone.now().date() - timedelta(days=30)

    # Group daily rollups by meter's energy_source
    mix_data = (
        DailyRollup.objects.filter(meter__facility=facility, rollup_date__gte=cutoff)
        .values('meter__energy_source')
        .annotate(total_kwh=Sum('total_energy_kwh'))
        .order_by('meter__energy_source')
    )

    grand_total = sum((m['total_kwh'] or Decimal('0.0000')) for m in mix_data)
    sources = []
    for m in mix_data:
        kwh = m['total_kwh'] or Decimal('0.0000')
        share = round((kwh / grand_total * Decimal('100.0')), 2) if grand_total > 0 else Decimal('0.00')
        sources.append({
            'source': m['meter__energy_source'],
            'energy_kwh': kwh,
            'percentage': share
        })

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'total_consumption_kwh': grand_total,
        'energy_mix': sources
    }

def get_facility_load_breakdown(facility_id: int, user) -> dict:
    facility = get_facility_for_user(facility_id, user)
    cutoff = timezone.now().date() - timedelta(days=30)

    # Group daily rollups by sub-meter load_category (excluding main_incomer)
    sub_loads = (
        DailyRollup.objects.filter(
            meter__facility=facility,
            rollup_date__gte=cutoff,
        )
        .exclude(meter__load_category='main_incomer')
        .values('meter__load_category')
        .annotate(total_kwh=Sum('total_energy_kwh'))
        .order_by('meter__load_category')
    )

    total_sub_kwh = sum((l['total_kwh'] or Decimal('0.0000')) for l in sub_loads)
    breakdown = []
    for l in sub_loads:
        kwh = l['total_kwh'] or Decimal('0.0000')
        share = round((kwh / total_sub_kwh * Decimal('100.0')), 2) if total_sub_kwh > 0 else Decimal('0.00')
        breakdown.append({
            'load_category': l['meter__load_category'],
            'energy_kwh': kwh,
            'percentage': share
        })

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'total_submetered_kwh': total_sub_kwh,
        'breakdown': breakdown
    }
