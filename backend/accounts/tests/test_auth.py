import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser, AuditLog

@pytest.fixture
def test_user(db):
    return CustomUser.objects.create_user(
        email='customer@alphatech.in',
        password='TestPassword123!',
        role='customer',
        first_name='Rajesh',
        last_name='Sharma'
    )

@pytest.mark.django_db
def test_csrf_token_endpoint():
    client = APIClient()
    response = client.get('/api/v1/accounts/csrf/')
    assert response.status_code == 200
    assert 'csrfToken' in response.json()
    assert 'csrftoken' in response.cookies

@pytest.mark.django_db
def test_successful_login(test_user):
    client = APIClient()
    response = client.post('/api/v1/accounts/login/', {
        'email': 'customer@alphatech.in',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == 'customer@alphatech.in'
    assert data['role'] == 'customer'
    assert 'sessionid' in response.cookies

    # Verify audit log was created
    assert AuditLog.objects.filter(user=test_user, action='LOGIN_SUCCESS').exists()

@pytest.mark.django_db
def test_login_invalid_password(test_user):
    client = APIClient()
    response = client.post('/api/v1/accounts/login/', {
        'email': 'customer@alphatech.in',
        'password': 'WrongPassword999!'
    })
    assert response.status_code == 401
    data = response.json()
    assert data['error']['code'] == 'INVALID_CREDENTIALS'

@pytest.mark.django_db
def test_current_user_profile(test_user):
    client = APIClient()
    client.force_login(test_user)
    response = client.get('/api/v1/accounts/me/')
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == test_user.email
    assert data['full_name'] == 'Rajesh Sharma'

@pytest.mark.django_db
def test_logout(test_user):
    client = APIClient()
    client.force_login(test_user)
    response = client.post('/api/v1/accounts/logout/')
    assert response.status_code == 200
    assert response.json()['status'] == 'logged_out'

@pytest.mark.django_db
def test_change_password(test_user):
    client = APIClient()
    client.force_login(test_user)
    response = client.post('/api/v1/accounts/change-password/', {
        'old_password': 'TestPassword123!',
        'new_password': 'NewStrongPassword@2026'
    })
    assert response.status_code == 200
    assert response.json()['status'] == 'password_changed'

    # Re-authenticate with new password
    test_user.refresh_from_db()
    assert test_user.check_password('NewStrongPassword@2026')
