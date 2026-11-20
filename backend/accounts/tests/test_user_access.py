import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from accounts.models import CustomUser, AuditLog
from facilities.models import Facility, UserFacilityAssignment


def _facility(name, code):
    return Facility.objects.create(
        name=name, code=code, facility_type='tech_park', gross_floor_area_sqm=Decimal('10000.00'),
        address='Road', city='Bengaluru', state='Karnataka', pin_code='560001',
    )


@pytest.fixture
def world(db):
    fa = _facility('Alpha Park', 'FAC-A')
    fb = _facility('Beta Mall', 'FAC-B')
    admin = CustomUser.objects.create_user(email='boss@gg.in', password='pass12345', role='admin')
    eng = CustomUser.objects.create_user(email='eng@gg.in', password='pass12345', role='field_engineer')
    UserFacilityAssignment.objects.create(user=eng, facility=fa)
    cust = CustomUser.objects.create_user(email='cust@gg.in', password='pass12345', role='customer')
    UserFacilityAssignment.objects.create(user=cust, facility=fa)
    other_cust = CustomUser.objects.create_user(email='other@gg.in', password='pass12345', role='customer')
    UserFacilityAssignment.objects.create(user=other_cust, facility=fb)
    return {'fa': fa, 'fb': fb, 'admin': admin, 'eng': eng, 'cust': cust, 'other': other_cust}


def _client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _payload(email, role='customer', facility_ids=None, **extra):
    d = {'email': email, 'password': 'TempPass#2026', 'role': role, 'first_name': 'New', 'last_name': 'User'}
    if facility_ids is not None:
        d['facility_ids'] = facility_ids
    d.update(extra)
    return d


# ---------- creating users ----------

@pytest.mark.django_db
def test_admin_creates_customer_with_facilities(world):
    res = _client(world['admin']).post('/api/v1/accounts/users/', _payload('c1@gg.in', facility_ids=[world['fa'].id, world['fb'].id]), format='json')
    assert res.status_code == 201
    assert sorted(res.json()['assigned_facility_ids']) == sorted([world['fa'].id, world['fb'].id])
    assert AuditLog.objects.filter(action='GRANT_FACILITY_ACCESS', user=world['admin']).exists()


@pytest.mark.django_db
def test_admin_creates_field_engineer_but_not_admin(world):
    c = _client(world['admin'])
    assert c.post('/api/v1/accounts/users/', _payload('e1@gg.in', role='field_engineer', facility_ids=[world['fa'].id]), format='json').status_code == 201
    res = c.post('/api/v1/accounts/users/', _payload('a1@gg.in', role='admin'), format='json')
    assert res.status_code == 403
    assert res.json()['error']['code'] == 'PERMISSION_DENIED'


@pytest.mark.django_db
def test_admin_unknown_facility_is_validation_error(world):
    res = _client(world['admin']).post('/api/v1/accounts/users/', _payload('c2@gg.in', facility_ids=[9999]), format='json')
    assert res.status_code == 400


@pytest.mark.django_db
def test_engineer_creates_customer_for_own_facility(world):
    res = _client(world['eng']).post('/api/v1/accounts/users/', _payload('c3@gg.in', facility_ids=[world['fa'].id]), format='json')
    assert res.status_code == 201
    assert res.json()['role'] == 'customer'
    assert res.json()['assigned_facility_ids'] == [world['fa'].id]


@pytest.mark.django_db
def test_engineer_cannot_grant_unassigned_facility(world):
    res = _client(world['eng']).post('/api/v1/accounts/users/', _payload('c4@gg.in', facility_ids=[world['fb'].id]), format='json')
    assert res.status_code == 404
    assert not CustomUser.objects.filter(email='c4@gg.in').exists()


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['field_engineer', 'admin'])
def test_engineer_can_only_create_customers(world, role):
    res = _client(world['eng']).post('/api/v1/accounts/users/', _payload(f'x_{role}@gg.in', role=role, facility_ids=[world['fa'].id]), format='json')
    assert res.status_code == 403


@pytest.mark.django_db
def test_engineer_must_pick_a_facility(world):
    res = _client(world['eng']).post('/api/v1/accounts/users/', _payload('c5@gg.in', facility_ids=[]), format='json')
    assert res.status_code == 400


@pytest.mark.django_db
def test_customer_cannot_create_users(world):
    res = _client(world['cust']).post('/api/v1/accounts/users/', _payload('c6@gg.in', facility_ids=[world['fa'].id]), format='json')
    assert res.status_code == 403


@pytest.mark.django_db
def test_duplicate_email_rejected(world):
    res = _client(world['admin']).post('/api/v1/accounts/users/', _payload('cust@gg.in', facility_ids=[world['fa'].id]), format='json')
    assert res.status_code == 400


# ---------- listing ----------

@pytest.mark.django_db
def test_admin_sees_all_users_engineer_sees_only_shared_customers(world):
    admin_emails = {u['email'] for u in _client(world['admin']).get('/api/v1/accounts/users/').json()['results']}
    assert {'cust@gg.in', 'other@gg.in', 'eng@gg.in'} <= admin_emails
    eng_emails = {u['email'] for u in _client(world['eng']).get('/api/v1/accounts/users/').json()['results']}
    assert eng_emails == {'cust@gg.in'}


# ---------- editing access ----------

@pytest.mark.django_db
def test_admin_replaces_facility_access(world):
    res = _client(world['admin']).put(f"/api/v1/accounts/users/{world['cust'].id}/facilities/", {'facility_ids': [world['fb'].id]}, format='json')
    assert res.status_code == 200
    assert res.json()['assigned_facility_ids'] == [world['fb'].id]
    assert AuditLog.objects.filter(action='UPDATE_FACILITY_ACCESS').exists()


@pytest.mark.django_db
def test_engineer_edits_only_within_own_scope_and_keeps_other_access(world):
    # customer also has Beta access granted by an admin; the engineer (Alpha only) must not drop it
    UserFacilityAssignment.objects.create(user=world['cust'], facility=world['fb'])
    fc = _facility('Gamma Hub', 'FAC-C')
    UserFacilityAssignment.objects.create(user=world['eng'], facility=fc)
    res = _client(world['eng']).put(f"/api/v1/accounts/users/{world['cust'].id}/facilities/", {'facility_ids': [fc.id]}, format='json')
    assert res.status_code == 200
    ids = set(UserFacilityAssignment.objects.filter(user=world['cust']).values_list('facility_id', flat=True))
    assert ids == {world['fb'].id, fc.id}  # Alpha removed (in scope), Beta kept (out of scope), Gamma added


@pytest.mark.django_db
def test_engineer_cannot_edit_users_outside_their_facilities(world):
    res = _client(world['eng']).put(f"/api/v1/accounts/users/{world['other'].id}/facilities/", {'facility_ids': [world['fa'].id]}, format='json')
    assert res.status_code == 404


@pytest.mark.django_db
def test_engineer_cannot_grant_unassigned_facility_when_editing(world):
    res = _client(world['eng']).put(f"/api/v1/accounts/users/{world['cust'].id}/facilities/", {'facility_ids': [world['fb'].id]}, format='json')
    assert res.status_code == 404


@pytest.mark.django_db
def test_customer_cannot_edit_access(world):
    res = _client(world['cust']).put(f"/api/v1/accounts/users/{world['cust'].id}/facilities/", {'facility_ids': [world['fa'].id]}, format='json')
    assert res.status_code == 403


@pytest.mark.django_db
def test_only_admin_can_deactivate_users(world):
    url = f"/api/v1/accounts/users/{world['cust'].id}/"
    assert _client(world['eng']).patch(url, {'is_active': False}, format='json').status_code == 403
    assert _client(world['admin']).patch(url, {'is_active': False}, format='json').status_code == 200
    world['cust'].refresh_from_db()
    assert world['cust'].is_active is False
