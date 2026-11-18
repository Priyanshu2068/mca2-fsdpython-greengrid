"""
GreenGrid Facilities Services (Mutations & Key Management).
"""

import secrets
import hashlib
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from facilities.models import Facility, Building, Meter, DataSource, UserFacilityAssignment

def hash_api_key(raw_key: str) -> str:
    """Computes SHA-256 hex digest of the raw secret API key."""
    return hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

@transaction.atomic
def create_facility(data: dict) -> Facility:
    code = data.get('code', '').strip().upper()
    if Facility.objects.filter(code=code).exists():
        raise ValidationError({'code': ['A facility with this unique code already exists.']})
    data['code'] = code
    return Facility.objects.create(**data)

def create_building(facility: Facility, name: str, code: str, floor_area_sqm, total_floors=1) -> Building:
    code_clean = code.strip().upper()
    if Building.objects.filter(facility=facility, code=code_clean).exists():
        raise ValidationError({'code': ['Building code must be unique within this facility.']})
    return Building.objects.create(
        facility=facility,
        name=name,
        code=code_clean,
        floor_area_sqm=floor_area_sqm,
        total_floors=total_floors
    )

def register_meter(facility: Facility, data: dict) -> Meter:
    meter_identifier = data.get('meter_identifier', '').strip().upper()
    if Meter.objects.filter(meter_identifier=meter_identifier).exists():
        raise ValidationError({'meter_identifier': ['A meter with this identifier is already registered.']})
    data['facility'] = facility
    data['meter_identifier'] = meter_identifier
    return Meter.objects.create(**data)

def generate_datasource_api_key(facility: Facility, name: str) -> tuple[DataSource, str]:
    """
    Generates a secure cryptographically random API key for device ingestion.
    Returns (datasource_instance, raw_key_secret).
    The raw_key_secret is only displayed once and NEVER stored plain in the database.
    """
    prefix = f"gg_{secrets.token_hex(4)}"
    token = secrets.token_urlsafe(32)
    raw_key = f"{prefix}_{token}"
    key_hash = hash_api_key(raw_key)

    datasource = DataSource.objects.create(
        facility=facility,
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        is_active=True
    )
    return datasource, raw_key

def rotate_datasource_api_key(datasource: DataSource) -> str:
    """
    Rotates existing DataSource credentials, invalidating the previous API key.
    Returns new raw_key_secret.
    """
    prefix = f"gg_{secrets.token_hex(4)}"
    token = secrets.token_urlsafe(32)
    new_raw_key = f"{prefix}_{token}"

    datasource.key_prefix = prefix
    datasource.key_hash = hash_api_key(new_raw_key)
    datasource.last_used_at = None
    datasource.save(update_fields=['key_prefix', 'key_hash', 'last_used_at'])

    return new_raw_key

def validate_api_key(raw_key: str) -> DataSource | None:
    """
    Validates incoming X-API-Key header against active DataSources.
    """
    if not raw_key or not isinstance(raw_key, str):
        return None
    key_hash = hash_api_key(raw_key)
    try:
        ds = DataSource.objects.select_related('facility').get(key_hash=key_hash, is_active=True)
        ds.last_used_at = timezone.now()
        ds.save(update_fields=['last_used_at'])
        return ds
    except DataSource.DoesNotExist:
        return None
