import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, UserFacilityAssignment

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_superuser(
        email='admin@greengrid.in',
        password='AdminPassword123!',
        first_name='Admin',
        last_name='User'
    )

@pytest.fixture
def customer_user(db):
    return CustomUser.objects.create_user(
        email='cust@alphatech.in',
        password='CustomerPass123!',
        role='customer',
        first_name='Customer',
        last_name='User'
    )

@pytest.fixture
def facilities(db, customer_user):
    f1 = Facility.objects.create(
        name='Alpha Tech Park',
        code='FAC-BLR-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('45000.00'),
        operating_hours_per_week=Decimal('65.00'),
        address='Bellandur, ORR',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560103',
        sanctioned_demand_kva=Decimal('2500.00')
    )
    f2 = Facility.objects.create(
        name='Pune Infotech City',
        code='FAC-PUN-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('38000.00'),
        operating_hours_per_week=Decimal('60.00'),
        address='Hinjewadi Phase 1',
        city='Pune',
        state='Maharashtra',
        pin_code='411057',
        sanctioned_demand_kva=Decimal('2000.00')
    )
    # Assign f1 to customer_user
    UserFacilityAssignment.objects.create(user=customer_user, facility=f1)
    return f1, f2

@pytest.mark.django_db
def test_admin_sees_all_facilities(admin_user, facilities):
    client = APIClient()
    client.force_login(admin_user)
    response = client.get('/api/v1/facilities/')
    assert response.status_code == 200
    assert response.json()['count'] == 2

@pytest.mark.django_db
def test_customer_scoped_to_assigned_facility_only(customer_user, facilities):
    f1, f2 = facilities
    client = APIClient()
    client.force_login(customer_user)
    response = client.get('/api/v1/facilities/')
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['id'] == f1.id

@pytest.mark.django_db
def test_customer_cannot_access_unassigned_facility_returns_404(customer_user, facilities):
    f1, f2 = facilities
    client = APIClient()
    client.force_login(customer_user)
    # Access f2 which is NOT assigned to customer
    response = client.get(f'/api/v1/facilities/{f2.id}/')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'RESOURCE_NOT_FOUND'
