import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter
from facilities.services import generate_datasource_api_key
from ingestion.models import RawReading, BatchLog

@pytest.fixture
def facility_meter(db):
    fac = Facility.objects.create(
        name='Alpha Tech Park',
        code='FAC-BLR-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('45000.00'),
        operating_hours_per_week=Decimal('65.00'),
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
    datasource, raw_key = generate_datasource_api_key(fac, name='Test Gateway')
    return fac, meter, datasource, raw_key

@pytest.mark.django_db
def test_bulk_ingestion_via_api_key(facility_meter):
    fac, meter, datasource, raw_key = facility_meter
    client = APIClient()

    payload = {
        'readings': [
            {
                'meter_identifier': meter.meter_identifier,
                'timestamp': '2026-03-30T10:00:00Z',
                'energy_kwh': '42.5000',
                'active_power_kw': '170.0000',
                'voltage_v': '415.00',
                'current_a': '248.50',
                'power_factor': '0.950',
                'frequency_hz': '50.00'
            },
            {
                'meter_identifier': meter.meter_identifier,
                'timestamp': '2026-03-30T10:15:00Z',
                'energy_kwh': '43.0000',
                'active_power_kw': '172.0000',
                'voltage_v': '415.20',
                'current_a': '250.10',
                'power_factor': '0.950',
                'frequency_hz': '49.98'
            }
        ]
    }

    response = client.post(
        '/api/v1/ingestion/readings/bulk/',
        payload,
        format='json',
        HTTP_X_API_KEY=raw_key
    )
    assert response.status_code == 201
    data = response.json()
    assert data['accepted'] == 2
    assert data['duplicates_ignored'] == 0
    assert data['rejected'] == 0
    assert RawReading.objects.filter(meter=meter).count() == 2

@pytest.mark.django_db
def test_ingestion_idempotency_duplicates_ignored(facility_meter):
    fac, meter, datasource, raw_key = facility_meter
    client = APIClient()

    payload = {
        'readings': [
            {
                'meter_identifier': meter.meter_identifier,
                'timestamp': '2026-03-30T11:00:00Z',
                'energy_kwh': '50.0000',
                'active_power_kw': '200.0000',
                'power_factor': '0.960'
            }
        ]
    }

    # First transmission
    r1 = client.post('/api/v1/ingestion/readings/bulk/', payload, format='json', HTTP_X_API_KEY=raw_key)
    assert r1.status_code == 201
    assert r1.json()['accepted'] == 1
    assert r1.json()['duplicates_ignored'] == 0

    # Second transmission of identical reading -> idempotent, duplicate ignored
    r2 = client.post('/api/v1/ingestion/readings/bulk/', payload, format='json', HTTP_X_API_KEY=raw_key)
    assert r2.status_code == 201
    assert r2.json()['accepted'] == 0
    assert r2.json()['duplicates_ignored'] == 1
    assert RawReading.objects.filter(meter=meter).count() == 1

@pytest.mark.django_db
def test_invalid_api_key_returns_401(facility_meter):
    client = APIClient()
    response = client.post(
        '/api/v1/ingestion/readings/bulk/',
        {'readings': []},
        format='json',
        HTTP_X_API_KEY='gg_invalid_secret_key'
    )
    assert response.status_code == 401
    assert response.json()['error']['code'] == 'INVALID_API_KEY'

@pytest.mark.django_db
def test_batch_limit_exceeded_rejected():
    client = APIClient()
    # Mock oversize payload > 5000 items
    oversize = [{'meter_identifier': 'M1', 'timestamp': '2026-03-30T10:00:00Z', 'energy_kwh': '1.0'} for _ in range(5001)]
    # Use dummy admin user
    user = CustomUser.objects.create_superuser(email='adm@gg.in', password='pass')
    client.force_login(user)
    response = client.post('/api/v1/ingestion/readings/bulk/', {'readings': oversize}, format='json')
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'VALIDATION_ERROR'
