import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter, UserFacilityAssignment
from ingestion.models import RawReading
from analytics.models import HourlyRollup, AnomalyAlert
from analytics.services import run_anomaly_detection

@pytest.fixture
def setup_facility(db):
    user = CustomUser.objects.create_superuser(email='adm@gg.in', password='pass')
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
    incomer = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    dg = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-DG',
        name='Backup DG Set',
        energy_source='diesel_generator',
        load_category='main_incomer'
    )
    return user, fac, incomer, dg

@pytest.mark.django_db
def test_consumption_spike_anomaly_detection(setup_facility):
    user, fac, incomer, dg = setup_facility
    now = timezone.now().replace(minute=0, second=0, microsecond=0)

    # Create 4 past weekly baselines for this hour with ~100 kWh
    for w in (1, 2, 3, 4):
        HourlyRollup.objects.create(
            meter=incomer,
            bucket_start=now - timedelta(weeks=w),
            total_energy_kwh=Decimal('100.0000'),
            peak_demand_kw=Decimal('120.0000'),
            avg_power_factor=Decimal('0.950'),
            reading_count=4
        )

    # Current hour has spike of 160 kWh (> 1.3x 100 kWh baseline)
    HourlyRollup.objects.create(
        meter=incomer,
        bucket_start=now,
        total_energy_kwh=Decimal('160.0000'),
        peak_demand_kw=Decimal('200.0000'),
        avg_power_factor=Decimal('0.950'),
        reading_count=4
    )

    alerts = run_anomaly_detection()
    spike_alert = next((a for a in alerts if a.anomaly_type == 'consumption_spike'), None)
    assert spike_alert is not None
    assert spike_alert.meter == incomer
    assert spike_alert.deviation_factor == Decimal('1.60')

@pytest.mark.django_db
def test_low_power_factor_anomaly_detection(setup_facility):
    user, fac, incomer, dg = setup_facility
    now = timezone.now().replace(minute=0, second=0, microsecond=0)

    HourlyRollup.objects.create(
        meter=incomer,
        bucket_start=now,
        total_energy_kwh=Decimal('50.0000'),
        peak_demand_kw=Decimal('60.0000'),
        avg_power_factor=Decimal('0.820'), # Below 0.900 threshold
        reading_count=4
    )

    alerts = run_anomaly_detection()
    pf_alert = next((a for a in alerts if a.anomaly_type == 'low_power_factor'), None)
    assert pf_alert is not None
    assert pf_alert.severity == 'high'

@pytest.mark.django_db
def test_dg_grid_clash_anomaly_detection(setup_facility):
    user, fac, incomer, dg = setup_facility
    now = timezone.now()

    # Incomer has grid voltage 415 V
    RawReading.objects.create(
        meter=incomer,
        timestamp=now - timedelta(minutes=10),
        energy_kwh=Decimal('30.0000'),
        active_power_kw=Decimal('120.0000'),
        voltage_v=Decimal('415.00')
    )
    # DG is running at 150 kW simultaneously!
    RawReading.objects.create(
        meter=dg,
        timestamp=now - timedelta(minutes=10),
        energy_kwh=Decimal('37.5000'),
        active_power_kw=Decimal('150.0000'),
        voltage_v=Decimal('415.00')
    )

    alerts = run_anomaly_detection()
    clash_alert = next((a for a in alerts if a.anomaly_type == 'dg_grid_clash'), None)
    assert clash_alert is not None
    assert clash_alert.severity == 'critical'

@pytest.mark.django_db
def test_alert_acknowledge_api(setup_facility):
    user, fac, incomer, dg = setup_facility
    alert = AnomalyAlert.objects.create(
        facility=fac,
        meter=incomer,
        anomaly_type='low_power_factor',
        severity='high',
        reason='PF dropped to 0.820.',
        status='open'
    )

    client = APIClient()
    client.force_login(user)

    response = client.patch(f'/api/v1/analytics/alerts/{alert.id}/', {
        'status': 'acknowledged',
        'resolution_notes': 'Maintenance team notified.'
    })
    assert response.status_code == 200
    alert.refresh_from_db()
    assert alert.status == 'acknowledged'
    assert alert.resolution_notes == 'Maintenance team notified.'



@pytest.mark.django_db
@pytest.mark.parametrize('role,expected', [('field_engineer', 200), ('admin', 200), ('customer', 403)])
def test_alert_update_is_role_restricted(setup_facility, role, expected):
    _, fac, incomer, _ = setup_facility
    user = CustomUser.objects.create_user(email=f'{role}@gg.in', password='pass', role=role)
    UserFacilityAssignment.objects.create(user=user, facility=fac)
    alert = AnomalyAlert.objects.create(
        facility=fac, meter=incomer, anomaly_type='low_power_factor',
        severity='high', reason='PF dropped.', status='open'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.patch(f'/api/v1/analytics/alerts/{alert.id}/', {'status': 'acknowledged'})
    assert res.status_code == expected
    if expected == 403:
        assert res.json()['error']['code'] == 'PERMISSION_DENIED'
        alert.refresh_from_db()
        assert alert.status == 'open'


@pytest.mark.django_db
def test_idle_solar_and_diesel_meters_are_not_reported_silent(setup_facility):
    """Solar sleeps at night and a diesel generator is idle until an outage: neither is an anomaly."""
    _, fac, incomer, dg = setup_facility
    solar = Meter.objects.create(
        facility=fac, meter_identifier='MTR-SOL', name='Rooftop Solar', energy_source='solar', load_category='main_incomer')
    long_ago = timezone.now() - timedelta(hours=10)
    for m in (incomer, dg, solar):
        RawReading.objects.create(
            meter=m, timestamp=long_ago, energy_kwh=Decimal('1.0000'), active_power_kw=Decimal('4.0000'),
            power_factor=Decimal('0.950'), voltage_v=Decimal('415.00'))

    alerts = run_anomaly_detection()
    silent = {a.meter_id for a in alerts if a.anomaly_type == 'meter_silent'}
    assert incomer.id in silent          # a grid meter that stopped reporting is still flagged
    assert dg.id not in silent
    assert solar.id not in silent
