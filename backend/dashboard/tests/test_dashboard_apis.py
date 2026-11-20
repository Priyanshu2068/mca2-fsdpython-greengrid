import pytest
import time
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter, UserFacilityAssignment
from analytics.models import HourlyRollup, DailyRollup, AnomalyAlert

@pytest.fixture
def dashboard_setup(db):
    user = CustomUser.objects.create_user(email='customer@alpha.in', password='pass', role='customer')
    fac = Facility.objects.create(
        name='Alpha Tech Park',
        code='FAC-BLR-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('45000.00'),
        sanctioned_demand_kva=Decimal('2500.00'),
        address='Bellandur',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560103'
    )
    UserFacilityAssignment.objects.create(user=user, facility=fac)

    # Incomer meter
    incomer = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    # Sub-meter HVAC
    hvac = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-HVAC',
        name='HVAC Chiller',
        energy_source='grid',
        load_category='hvac'
    )

    now = timezone.now()
    today = timezone.localtime(now).date()
    yesterday = today - timedelta(days=1)
    # UTC hour buckets straddle local midnight (IST is UTC+5:30), so clamp the bucket to local midnight
    local_midnight = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    today_bucket = max(now.replace(minute=0, second=0, microsecond=0), local_midnight)

    # Yesterday daily rollup: 1000 kWh
    DailyRollup.objects.create(
        meter=incomer,
        rollup_date=yesterday,
        total_energy_kwh=Decimal('1000.0000'),
        peak_demand_kw=Decimal('250.0000')
    )
    # Today hourly rollup: 500 kWh, peak 300 kW
    HourlyRollup.objects.create(
        meter=incomer,
        bucket_start=today_bucket,
        total_energy_kwh=Decimal('500.0000'),
        peak_demand_kw=Decimal('300.0000')
    )
    # Sub-meter daily rollup: 400 kWh HVAC
    DailyRollup.objects.create(
        meter=hvac,
        rollup_date=today,
        total_energy_kwh=Decimal('400.0000'),
        peak_demand_kw=Decimal('120.0000')
    )
    # Open alert
    AnomalyAlert.objects.create(
        facility=fac,
        meter=incomer,
        anomaly_type='low_power_factor',
        severity='medium',
        reason='PF dropped',
        status='open'
    )
    return user, fac

@pytest.mark.django_db
def test_dashboard_summary_kpi_calculation_and_latency(dashboard_setup):
    user, fac = dashboard_setup
    client = APIClient()
    client.force_login(user)

    start = time.perf_counter()
    response = client.get(f'/api/v1/dashboard/summary/?facility_id={fac.id}')
    duration = time.perf_counter() - start

    assert response.status_code == 200
    # Must guarantee sub-second (< 1.0 s) response
    assert duration < 1.0

    data = response.json()
    metrics = data['metrics']
    assert Decimal(str(metrics['today_consumption_kwh'])) == Decimal('500.0000')
    assert Decimal(str(metrics['yesterday_same_time_kwh'])) == Decimal('1000.0000')
    assert Decimal(str(metrics['current_peak_demand_kw'])) == Decimal('300.0000')
    assert metrics['active_anomalies_count'] == 1

@pytest.mark.django_db
def test_dashboard_trends_24h_and_30d(dashboard_setup):
    user, fac = dashboard_setup
    client = APIClient()
    client.force_login(user)

    r_24h = client.get(f'/api/v1/dashboard/trends/?facility_id={fac.id}&range=24h')
    assert r_24h.status_code == 200
    assert len(r_24h.json()['points']) >= 1

    r_30d = client.get(f'/api/v1/dashboard/trends/?facility_id={fac.id}&range=30d')
    assert r_30d.status_code == 200
    assert len(r_30d.json()['points']) >= 1

@pytest.mark.django_db
def test_dashboard_load_breakdown(dashboard_setup):
    user, fac = dashboard_setup
    client = APIClient()
    client.force_login(user)

    response = client.get(f'/api/v1/dashboard/load-breakdown/?facility_id={fac.id}')
    assert response.status_code == 200
    data = response.json()
    assert len(data['breakdown']) >= 1
    assert data['breakdown'][0]['load_category'] == 'hvac'

@pytest.mark.django_db
def test_unassigned_facility_returns_404(dashboard_setup):
    user, fac = dashboard_setup
    # Create another unassigned facility
    other_fac = Facility.objects.create(
        name='Pune City', code='FAC-PUN-02', facility_type='tech_park',
        gross_floor_area_sqm=Decimal('20000.00'), address='Hinjewadi', city='Pune', state='MH', pin_code='411057'
    )
    client = APIClient()
    client.force_login(user)

    response = client.get(f'/api/v1/dashboard/summary/?facility_id={other_fac.id}')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'RESOURCE_NOT_FOUND'


@pytest.mark.django_db
def test_dashboard_summary_reports_when_the_newest_data_is_from(dashboard_setup):
    user, fac = dashboard_setup
    client = APIClient()
    client.force_login(user)
    data = client.get(f'/api/v1/dashboard/summary/?facility_id={fac.id}').json()
    assert data['latest_data_at'] is not None  # the fixture has hourly rollups

    # a facility with no rollups yet reports null instead of failing
    from facilities.models import Facility
    empty = Facility.objects.create(
        name='Empty Site', code='FAC-EMPTY', facility_type='tech_park', gross_floor_area_sqm=Decimal('1000.00'),
        address='x', city='x', state='x', pin_code='1')
    UserFacilityAssignment.objects.create(user=user, facility=empty)
    assert client.get(f'/api/v1/dashboard/summary/?facility_id={empty.id}').json()['latest_data_at'] is None
