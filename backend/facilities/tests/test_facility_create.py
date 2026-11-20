import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser, AuditLog
from facilities.models import Facility


def _payload(code='new-hq-01', **extra):
    d = {
        'name': 'New HQ', 'code': code, 'facility_type': 'commercial_office',
        'gross_floor_area_sqm': '12000.00', 'sanctioned_demand_kva': '800.00',
        'operating_hours_per_week': '60.00', 'address': '1 Main Road',
        'city': 'Pune', 'state': 'Maharashtra', 'pin_code': '411001',
    }
    d.update(extra)
    return d


def _client(role):
    user = CustomUser.objects.create_user(email=f'{role}@fac.in', password='pass12345', role=role)
    c = APIClient()
    c.force_authenticate(user=user)
    return c, user


@pytest.mark.django_db
def test_admin_creates_facility_and_gets_it_back():
    c, admin = _client('admin')
    res = c.post('/api/v1/facilities/', _payload(), format='json')
    assert res.status_code == 201
    body = res.json()
    assert body['id'] and body['code'] == 'NEW-HQ-01'  # code is normalised to upper case
    assert Facility.objects.filter(id=body['id']).exists()
    assert AuditLog.objects.filter(action='CREATE_FACILITY', user=admin).exists()


@pytest.mark.django_db
def test_duplicate_code_is_rejected():
    c, _ = _client('admin')
    assert c.post('/api/v1/facilities/', _payload(), format='json').status_code == 201
    assert c.post('/api/v1/facilities/', _payload(code='NEW-HQ-01'), format='json').status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('field,value', [
    ('gross_floor_area_sqm', '0'), ('gross_floor_area_sqm', '-5'),
    ('sanctioned_demand_kva', '0'), ('operating_hours_per_week', '200'),
])
def test_invalid_sizes_are_rejected(field, value):
    c, _ = _client('admin')
    assert c.post('/api/v1/facilities/', _payload(**{field: value}), format='json').status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['field_engineer', 'customer'])
def test_only_admin_can_create_facility(role):
    c, _ = _client(role)
    res = c.post('/api/v1/facilities/', _payload(), format='json')
    assert res.status_code == 403
    assert not Facility.objects.filter(code='NEW-HQ-01').exists()
