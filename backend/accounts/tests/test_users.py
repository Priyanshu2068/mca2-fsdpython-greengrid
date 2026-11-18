import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser, AuditLog

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
        first_name='Cust',
        last_name='User'
    )

@pytest.mark.django_db
def test_admin_can_create_user(admin_user):
    client = APIClient()
    client.force_login(admin_user)
    response = client.post('/api/v1/accounts/users/', {
        'email': 'engineer.blr@greengrid.in',
        'password': 'EngineerPassword123!',
        'role': 'field_engineer',
        'first_name': 'Karthik',
        'last_name': 'Nair'
    })
    assert response.status_code == 201
    data = response.json()
    assert data['email'] == 'engineer.blr@greengrid.in'
    assert data['role'] == 'field_engineer'

    # Check audit log
    assert AuditLog.objects.filter(user=admin_user, action='CREATE_USER').exists()

@pytest.mark.django_db
def test_non_admin_cannot_access_user_management(customer_user):
    client = APIClient()
    client.force_login(customer_user)
    response = client.get('/api/v1/accounts/users/')
    assert response.status_code == 403
    assert response.json()['error']['code'] == 'PERMISSION_DENIED'

@pytest.mark.django_db
def test_admin_can_view_audit_logs(admin_user):
    client = APIClient()
    client.force_login(admin_user)
    AuditLog.objects.create(
        user=admin_user,
        action='CONFIG_CHANGE',
        resource_type='System',
        resource_id='1'
    )
    response = client.get('/api/v1/accounts/audit-logs/')
    assert response.status_code == 200
    assert len(response.json()) >= 1
