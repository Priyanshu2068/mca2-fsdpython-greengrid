import pytest
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.mark.django_db
def test_health_check_endpoint():
    client = APIClient()
    response = client.get('/api/v1/health/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert 'version' in data
    assert 'timestamp' in data

def test_openapi_schema_endpoint():
    client = APIClient()
    response = client.get('/api/schema/')
    assert response.status_code == 200

def test_swagger_ui_endpoint():
    client = APIClient()
    response = client.get('/api/docs/')
    assert response.status_code == 200
    assert b'swagger-ui' in response.content.lower()
