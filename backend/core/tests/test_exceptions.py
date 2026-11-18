import pytest
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response
from django.urls import path
from config.urls import urlpatterns

from rest_framework.permissions import AllowAny

class DummyErrorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error_type = request.query_params.get('type')
        if error_type == 'validation':
            raise ValidationError({'energy_kwh': ['Must be non-negative.']})
        elif error_type == 'permission':
            raise PermissionDenied('You do not have permission to perform this action.')
        elif error_type == 'not_found':
            raise NotFound('The requested facility was not found.')
        return Response({'ok': True})

urlpatterns.append(path('api/v1/test-error/', DummyErrorView.as_view()))

def test_validation_error_envelope():
    client = APIClient()
    response = client.get('/api/v1/test-error/?type=validation')
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert data['error']['status'] == 400
    assert data['error']['code'] == 'VALIDATION_ERROR'
    assert 'details' in data['error']

def test_permission_denied_envelope():
    client = APIClient()
    response = client.get('/api/v1/test-error/?type=permission')
    assert response.status_code == 403
    data = response.json()
    assert 'error' in data
    assert data['error']['status'] == 403
    assert data['error']['code'] == 'PERMISSION_DENIED'

def test_not_found_envelope():
    client = APIClient()
    response = client.get('/api/v1/test-error/?type=not_found')
    assert response.status_code == 404
    data = response.json()
    assert 'error' in data
    assert data['error']['status'] == 404
    assert data['error']['code'] == 'RESOURCE_NOT_FOUND'
