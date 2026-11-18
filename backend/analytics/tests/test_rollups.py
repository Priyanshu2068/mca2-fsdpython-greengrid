import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from facilities.models import Facility, Meter
from ingestion.models import RawReading
from analytics.models import HourlyRollup, DailyRollup
from analytics.services import compute_hourly_rollups, compute_daily_rollups

@pytest.fixture
def meter_with_readings(db):
    fac = Facility.objects.create(
        name='Alpha Tech Park',
        code='FAC-BLR-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('45000.00'),
        address='Bellandur',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560103'
    )
    meter = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-BLR-01-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )

    # Top of the hour in active TIME_ZONE (Asia/Kolkata)
    base_time = timezone.localtime(timezone.now()).replace(minute=0, second=0, microsecond=0) - timedelta(hours=4)
    for i in range(4):
        RawReading.objects.create(
            meter=meter,
            timestamp=base_time + timedelta(minutes=15 * i),
            energy_kwh=Decimal('25.0000'),
            active_power_kw=Decimal('100.0000') + Decimal(str(i * 10)),
            power_factor=Decimal('0.950'),
            voltage_v=Decimal('415.00')
        )
    return meter, base_time

@pytest.mark.django_db
def test_hourly_rollup_computation(meter_with_readings):
    meter, base_time = meter_with_readings

    # Execute rollup
    count = compute_hourly_rollups(hours_back=24)
    assert count >= 1

    rollup = HourlyRollup.objects.filter(meter=meter).first()
    assert rollup is not None
    # 4 * 25.0 = 100.0 kWh
    assert rollup.total_energy_kwh == Decimal('100.0000')
    # Peak kW was 100 + 30 = 130.0 kW
    assert rollup.peak_demand_kw == Decimal('130.0000')
    assert rollup.min_demand_kw == Decimal('100.0000')
    assert rollup.reading_count == 4

    # Re-running is idempotent and updates cleanly
    count_rerun = compute_hourly_rollups(hours_back=24)
    assert count_rerun == count
    assert HourlyRollup.objects.filter(meter=meter).count() == 1

@pytest.mark.django_db
def test_daily_rollup_computation(meter_with_readings):
    meter, base_time = meter_with_readings
    compute_hourly_rollups(hours_back=24)

    # Execute daily rollup
    daily_count = compute_daily_rollups(days_back=3)
    assert daily_count >= 1

    daily = DailyRollup.objects.filter(meter=meter).first()
    assert daily is not None
    assert daily.total_energy_kwh == Decimal('100.0000')
    assert daily.peak_demand_kw == Decimal('130.0000')

