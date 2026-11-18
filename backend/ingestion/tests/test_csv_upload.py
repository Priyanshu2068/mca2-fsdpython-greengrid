import pytest
import io
from decimal import Decimal
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import CustomUser
from facilities.models import Facility, Meter
from ingestion.models import RawReading, BatchLog

@pytest.fixture
def engineer_with_meter(db):
    user = CustomUser.objects.create_user(
        email='eng.blr@greengrid.in',
        password='EngineerPass123!',
        role='field_engineer'
    )
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
    Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-BLR-01-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    from facilities.models import UserFacilityAssignment
    UserFacilityAssignment.objects.create(user=user, facility=fac)
    return user

@pytest.mark.django_db
def test_csv_upload_pipeline(engineer_with_meter):
    client = APIClient()
    client.force_login(engineer_with_meter)

    csv_content = (
        "meter_identifier,timestamp,energy_kwh,active_power_kw,power_factor,voltage_v\n"
        "MTR-BLR-01-INC,2026-03-30T12:00:00Z,45.5000,182.0000,0.950,415.00\n"
        "MTR-BLR-01-INC,2026-03-30T12:15:00Z,46.0000,184.0000,0.950,415.20\n"
    ).encode('utf-8')

    file = SimpleUploadedFile("readings.csv", csv_content, content_type="text/csv")

    response = client.post('/api/v1/ingestion/readings/upload-csv/', {'file': file}, format='multipart')
    assert response.status_code == 201
    data = response.json()
    assert data['accepted'] == 2
    assert data['duplicates_ignored'] == 0
    assert RawReading.objects.count() == 2
    assert BatchLog.objects.filter(source_type='csv_upload').exists()
