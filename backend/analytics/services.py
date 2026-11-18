"""
GreenGrid Analytics Services (Incremental Rollups & Rule-based Anomaly Engine).
"""

import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Max, Min, Avg, Count
from django.db.models.functions import TruncHour, TruncDate
from facilities.models import Meter, Facility
from ingestion.models import RawReading
from analytics.models import HourlyRollup, DailyRollup, AnomalyAlert

def compute_hourly_rollups(hours_back: int = 48) -> int:
    """
    Incremental 48-hour hourly rollup pipeline.
    Recomputes the past 48 hours to cleanly absorb delayed or backfilled readings.
    """
    now = timezone.now()
    cutoff = (now - timedelta(hours=hours_back)).replace(minute=0, second=0, microsecond=0)

    aggregates = (
        RawReading.objects.filter(timestamp__gte=cutoff)
        .annotate(hour_bucket=TruncHour('timestamp'))
        .values('meter_id', 'hour_bucket')
        .annotate(
            total_kwh=Sum('energy_kwh'),
            peak_kw=Max('active_power_kw'),
            min_kw=Min('active_power_kw'),
            avg_pf=Avg('power_factor'),
            count=Count('id')
        )
    )

    upsert_count = 0
    for row in aggregates:
        meter_id = row['meter_id']
        bucket = row['hour_bucket']
        total_kwh = Decimal(str(row['total_kwh'] or 0.0))
        peak_kw = Decimal(str(row['peak_kw'] or 0.0))
        min_kw = Decimal(str(row['min_kw'] or 0.0))
        avg_pf = Decimal(str(round(row['avg_pf'] or 1.0, 3)))
        count = row['count']

        HourlyRollup.objects.update_or_create(
            meter_id=meter_id,
            bucket_start=bucket,
            defaults={
                'total_energy_kwh': total_kwh,
                'peak_demand_kw': peak_kw,
                'min_demand_kw': min_kw,
                'avg_power_factor': avg_pf,
                'reading_count': count,
            }
        )
        upsert_count += 1

    return upsert_count

def compute_daily_rollups(days_back: int = 7) -> int:
    """
    Incremental daily rollup pipeline.
    Aggregates hourly buckets into daily totals with peak/off-peak segregation.
    """
    now = timezone.now()
    start_date = (now - timedelta(days=days_back)).date()

    hourly_rows = (
        HourlyRollup.objects.filter(bucket_start__date__gte=start_date)
        .select_related('meter')
        .order_by('meter_id', 'bucket_start')
    )

    daily_groups = {}
    for r in hourly_rows:
        d = r.bucket_start.date()
        key = (r.meter_id, d)
        if key not in daily_groups:
            daily_groups[key] = []
        daily_groups[key].append(r)

    upsert_count = 0
    for (meter_id, d), rows in daily_groups.items():
        total_kwh = sum(r.total_energy_kwh for r in rows)
        peak_kw = max(r.peak_demand_kw for r in rows)
        peak_reading = next((r for r in rows if r.peak_demand_kw == peak_kw), None)
        peak_ts = peak_reading.bucket_start if peak_reading else None

        # Indian DISCOM time-of-day: Off-peak (22:00-06:00), Peak (18:00-22:00)
        off_peak_kwh = sum(r.total_energy_kwh for r in rows if r.bucket_start.hour in [22, 23, 0, 1, 2, 3, 4, 5])
        peak_kwh = sum(r.total_energy_kwh for r in rows if r.bucket_start.hour in [18, 19, 20, 21])
        avg_pf = Decimal(str(round(sum(r.avg_power_factor for r in rows) / len(rows), 3)))
        reading_count = sum(r.reading_count for r in rows)

        DailyRollup.objects.update_or_create(
            meter_id=meter_id,
            rollup_date=d,
            defaults={
                'total_energy_kwh': total_kwh,
                'peak_demand_kw': peak_kw,
                'peak_timestamp': peak_ts,
                'off_peak_energy_kwh': off_peak_kwh,
                'peak_energy_kwh': peak_kwh,
                'avg_power_factor': avg_pf,
                'reading_count': reading_count,
            }
        )
        upsert_count += 1

    return upsert_count

def run_anomaly_detection() -> list:
    """
    Executes four deterministic anomaly detection rules:
    1. Consumption spike (> 1.3x 4-week hour-of-week median baseline and > 10.0 kWh)
    2. Power factor degradation (< 0.900)
    3. DG running while grid is nominal
    4. Meter silent for > 2 hours
    """
    now = timezone.now()
    generated_alerts = []

    # Rule 1 & Rule 2: Examine latest hourly rollups for all meters
    latest_hourly = (
        HourlyRollup.objects.filter(bucket_start__gte=now - timedelta(hours=3))
        .select_related('meter', 'meter__facility')
    )

    for rollup in latest_hourly:
        meter = rollup.meter
        facility = meter.facility
        bucket_time = rollup.bucket_start

        # --- Rule 1: Consumption Spike ---
        baseline_timestamps = [bucket_time - timedelta(weeks=w) for w in (1, 2, 3, 4)]
        past_values = list(
            HourlyRollup.objects.filter(meter=meter, bucket_start__in=baseline_timestamps)
            .values_list('total_energy_kwh', flat=True)
        )

        if past_values and len(past_values) >= 2:
            median_baseline = Decimal(str(statistics.median([float(v) for v in past_values])))
            if median_baseline > Decimal('5.0') and rollup.total_energy_kwh > (median_baseline * Decimal('1.30')):
                deviation = round(rollup.total_energy_kwh / median_baseline, 2)
                # Check for existing open alert
                if not AnomalyAlert.objects.filter(meter=meter, anomaly_type='consumption_spike', status='open').exists():
                    alert = AnomalyAlert.objects.create(
                        facility=facility,
                        meter=meter,
                        detected_at=bucket_time,
                        anomaly_type='consumption_spike',
                        severity='high' if deviation > Decimal('1.5') else 'medium',
                        reason=f"Observed energy of {rollup.total_energy_kwh} kWh is {deviation}x higher than 4-week median ({median_baseline:.2f} kWh) for {bucket_time.strftime('%A %H:00')}.",
                        baseline_value=median_baseline,
                        observed_value=rollup.total_energy_kwh,
                        deviation_factor=deviation
                    )
                    generated_alerts.append(alert)

        # --- Rule 2: Low Power Factor (< 0.900) ---
        if rollup.avg_power_factor < Decimal('0.900') and rollup.total_energy_kwh > Decimal('1.0'):
            if not AnomalyAlert.objects.filter(meter=meter, anomaly_type='low_power_factor', status='open').exists():
                alert = AnomalyAlert.objects.create(
                    facility=facility,
                    meter=meter,
                    detected_at=bucket_time,
                    anomaly_type='low_power_factor',
                    severity='high',
                    reason=f"Average power factor {rollup.avg_power_factor} fell below DISCOM threshold 0.900 on {meter.name}.",
                    baseline_value=Decimal('0.900'),
                    observed_value=rollup.avg_power_factor,
                    deviation_factor=round(Decimal('0.900') - rollup.avg_power_factor, 3)
                )
                generated_alerts.append(alert)

    # --- Rule 3: DG-Grid Clash ---
    recent_cutoff = now - timedelta(hours=2)
    dg_readings = (
        RawReading.objects.filter(
            meter__energy_source='diesel_generator',
            active_power_kw__gt=Decimal('10.00'),
            timestamp__gte=recent_cutoff
        ).select_related('meter', 'meter__facility')
    )

    for dg_r in dg_readings:
        fac = dg_r.meter.facility
        # Check if primary grid incomer had nominal voltage at that timestamp
        grid_incomer = RawReading.objects.filter(
            meter__facility=fac,
            meter__energy_source='grid',
            meter__load_category='main_incomer',
            timestamp__range=(dg_r.timestamp - timedelta(minutes=15), dg_r.timestamp + timedelta(minutes=15)),
            voltage_v__gte=Decimal('400.00')
        ).first()

        if grid_incomer and not AnomalyAlert.objects.filter(meter=dg_r.meter, anomaly_type='dg_grid_clash', status='open').exists():
            alert = AnomalyAlert.objects.create(
                facility=fac,
                meter=dg_r.meter,
                detected_at=dg_r.timestamp,
                anomaly_type='dg_grid_clash',
                severity='critical',
                reason=f"Diesel Generator {dg_r.meter.name} running ({dg_r.active_power_kw} kW) while main grid incomer voltage is nominal ({grid_incomer.voltage_v} V).",
                baseline_value=Decimal('0.0000'),
                observed_value=dg_r.active_power_kw,
                deviation_factor=Decimal('99.99')
            )
            generated_alerts.append(alert)

    # --- Rule 4: Meter Silent (> 2 Hours) ---
    active_meters = Meter.objects.filter(is_active=True).select_related('facility')
    two_hours_ago = now - timedelta(hours=2)
    for m in active_meters:
        last_reading = RawReading.objects.filter(meter=m).order_by('-timestamp').first()
        if last_reading and last_reading.timestamp < two_hours_ago:
            if not AnomalyAlert.objects.filter(meter=m, anomaly_type='meter_silent', status='open').exists():
                alert = AnomalyAlert.objects.create(
                    facility=m.facility,
                    meter=m,
                    detected_at=now,
                    anomaly_type='meter_silent',
                    severity='high',
                    reason=f"Meter '{m.meter_identifier}' has been silent for > 2 hours. Last reading received at {last_reading.timestamp.isoformat()}.",
                    baseline_value=Decimal('1.0000'),
                    observed_value=Decimal('0.0000'),
                    deviation_factor=Decimal('0.00')
                )
                generated_alerts.append(alert)

    return generated_alerts

