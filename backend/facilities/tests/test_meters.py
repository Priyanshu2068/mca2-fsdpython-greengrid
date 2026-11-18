import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter, DataSource, UserFacilityAssignment
from facilities.services import validate_api_key

@pytest.fixture
def engineer_user(db):
    user = CustomUser.objects.create_user(
        email='eng@greengrid.in',
        password='EngineerPass123!',
        role='field_engineer',
        first_name='Field',
        last_name='Engineer'
    )
    return user

@pytest.fixture
def facility_with_assignment(db, engineer_user):
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
    UserFacilityAssignment.objects.create(user=engineer_user, facility=fac)
    return fac

@pytest.mark.django_db
def test_field_engineer_can_register_meter(engineer_user, facility_with_assignment):
    client = APIClient()
    client.force_login(engineer_user)
    response = client.post(f'/api/v1/facilities/{facility_with_assignment.id}/meters/', {
        'meter_identifier': 'MTR-BLR-01-HVAC-NEW',
        'name': 'New Chiller Meter',
        'energy_source': 'grid',
        'load_category': 'hvac',
        'meter_make': 'Schneider Electric',
        'meter_model': 'PM5350',
        'ct_ratio': '200.00',
        'pt_ratio': '1.00',
        'physical_location': 'Basement Plant Room'
    })
    assert response.status_code == 201
    data = response.json()
    assert data['meter_identifier'] == 'MTR-BLR-01-HVAC-NEW'
    assert Meter.objects.filter(meter_identifier='MTR-BLR-01-HVAC-NEW').exists()

@pytest.mark.django_db
def test_generate_and_validate_datasource_api_key(engineer_user, facility_with_assignment):
    client = APIClient()
    client.force_login(engineer_user)
    response = client.post(f'/api/v1/facilities/{facility_with_assignment.id}/datasources/', {
        'name': 'Primary IoT Gateway'
    })
    assert response.status_code == 201
    data = response.json()
    assert 'api_key' in data
    raw_key = data['api_key']
    ds_id = data['datasource']['id']

    # Validate the raw key using the service
    ds = validate_api_key(raw_key)
    assert ds is not None
    assert ds.id == ds_id

    # Rotate the key
    rotate_res = client.post(f'/api/v1/facilities/datasources/{ds_id}/rotate-key/')
    assert rotate_res.status_code == 200
    new_raw_key = rotate_res.json()['new_api_key']
    assert new_raw_key != raw_key

    # Old key is invalidated
    assert validate_api_key(raw_key) is None
    # New key is active
    assert validate_api_key(new_raw_key) is not None
