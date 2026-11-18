"""
GreenGrid Ingestion Services (Idempotent Bulk Persistence & CSV Engine).
"""

import time
import secrets
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from facilities.models import Meter, Facility
from facilities.selectors import get_user_facility_ids
from ingestion.models import RawReading, BatchLog

def ingest_bulk_readings(readings_data: list, datasource=None, user=None, source_type='api_bulk') -> dict:
    """
    Ingests up to 5000 15-minute readings idempotently.
    Duplicates are ignored (ON CONFLICT DO NOTHING).
    Returns execution report with accepted, duplicate, and rejected counts.
    """
    start_time = time.perf_counter()
    max_batch = getattr(settings, 'INGESTION_MAX_BATCH_SIZE', 5000)

    if not readings_data:
        raise ValidationError({'readings': ['The readings batch payload cannot be empty.']})

    if len(readings_data) > max_batch:
        raise ValidationError({'readings': [f'Batch size ({len(readings_data)}) exceeds maximum permitted threshold of {max_batch} readings.']})

    batch_ref = f"BATCH-{timezone.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    # Cache meter lookups to optimize performance
    meter_identifiers = {item.get('meter_identifier', '').strip().upper() for item in readings_data if item.get('meter_identifier')}
    meters_by_id = {m.meter_identifier: m for m in Meter.objects.filter(meter_identifier__in=meter_identifiers).select_related('facility')}

    # Scoping validation
    scoped_facility_ids = None
    if datasource:
        scoped_facility_ids = [datasource.facility_id]
    elif user and not user.is_superuser and getattr(user, 'role', '') != 'admin':
        scoped_facility_ids = get_user_facility_ids(user)

    valid_instances = []
    rejections = []
    seen_in_batch = set()
    internal_batch_duplicates = 0

    for idx, item in enumerate(readings_data):
        identifier = str(item.get('meter_identifier', '')).strip().upper()
        raw_ts = item.get('timestamp')

        if not identifier:
            rejections.append({'index': idx, 'error': 'MISSING_METER_IDENTIFIER', 'reason': 'meter_identifier is required.'})
            continue

        meter = meters_by_id.get(identifier)
        if not meter:
            rejections.append({'index': idx, 'identifier': identifier, 'error': 'METER_NOT_FOUND', 'reason': f"Meter '{identifier}' is not registered."})
            continue

        if scoped_facility_ids is not None and meter.facility_id not in scoped_facility_ids:
            rejections.append({'index': idx, 'identifier': identifier, 'error': 'FACILITY_FORBIDDEN', 'reason': f"Meter '{identifier}' does not belong to your authorized facility."})
            continue

        # Parse timestamp
        try:
            if isinstance(raw_ts, datetime):
                parsed_ts = raw_ts if timezone.is_aware(raw_ts) else timezone.make_aware(raw_ts)
            else:
                parsed_ts = datetime.fromisoformat(str(raw_ts).replace('Z', '+00:00'))
                if timezone.is_naive(parsed_ts):
                    parsed_ts = timezone.make_aware(parsed_ts)
        except Exception:
            rejections.append({'index': idx, 'identifier': identifier, 'error': 'INVALID_TIMESTAMP', 'reason': f"Timestamp '{raw_ts}' is not valid ISO-8601."})
            continue

        # Check intra-batch duplicate
        batch_key = (meter.id, parsed_ts)
        if batch_key in seen_in_batch:
            internal_batch_duplicates += 1
            continue
        seen_in_batch.add(batch_key)

        # Validate numeric metrics
        try:
            energy_kwh = Decimal(str(item.get('energy_kwh', 0)))
            if energy_kwh < 0:
                rejections.append({'index': idx, 'identifier': identifier, 'error': 'INVALID_ENERGY', 'reason': 'energy_kwh must be non-negative.'})
                continue

            active_power_kw = Decimal(str(item.get('active_power_kw', 0)))
            reactive_power_kvar = Decimal(str(item.get('reactive_power_kvar', 0)))
            apparent_power_kva = Decimal(str(item.get('apparent_power_kva', 0)))
            voltage_v = Decimal(str(item.get('voltage_v', 415.00)))
            current_a = Decimal(str(item.get('current_a', 0.00)))
            power_factor = Decimal(str(item.get('power_factor', 1.000)))
            frequency_hz = Decimal(str(item.get('frequency_hz', 50.00)))

            if not (Decimal('0.000') <= power_factor <= Decimal('1.000')):
                rejections.append({'index': idx, 'identifier': identifier, 'error': 'INVALID_POWER_FACTOR', 'reason': 'power_factor must be between 0.0 and 1.0.'})
                continue
        except (InvalidOperation, TypeError, ValueError) as e:
            rejections.append({'index': idx, 'identifier': identifier, 'error': 'NUMERIC_PARSE_ERROR', 'reason': str(e)})
            continue

        valid_instances.append(RawReading(
            meter=meter,
            timestamp=parsed_ts,
            energy_kwh=energy_kwh,
            active_power_kw=active_power_kw,
            reactive_power_kvar=reactive_power_kvar,
            apparent_power_kva=apparent_power_kva,
            voltage_v=voltage_v,
            current_a=current_a,
            power_factor=power_factor,
            frequency_hz=frequency_hz
        ))

    # Determine existing duplicates in database prior to insert
    existing_in_db = 0
    if valid_instances:
        # Check existing (meter_id, timestamp) pairs
        meter_ids = {r.meter_id for r in valid_instances}
        timestamps = {r.timestamp for r in valid_instances}
        existing_keys = set(
            RawReading.objects.filter(meter_id__in=meter_ids, timestamp__in=timestamps)
            .values_list('meter_id', 'timestamp')
        )
        to_insert = [r for r in valid_instances if (r.meter_id, r.timestamp) not in existing_keys]
        existing_in_db = len(valid_instances) - len(to_insert)
    else:
        to_insert = []

    # Create BatchLog first to associate batch_id
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    batch_log = BatchLog.objects.create(
        datasource=datasource,
        uploaded_by=user if getattr(user, 'is_authenticated', False) else None,
        batch_reference=batch_ref,
        source_type=source_type,
        total_records=len(readings_data),
        accepted_records=len(to_insert),
        duplicate_records=existing_in_db + internal_batch_duplicates,
        rejected_records=len(rejections),
        ingestion_duration_ms=duration_ms,
        error_summary=rejections[:100]
    )

    if to_insert:
        for item in to_insert:
            item.batch = batch_log
        RawReading.objects.bulk_create(to_insert, ignore_conflicts=True)

    return {
        'batch_reference': batch_ref,
        'status': 'processed',
        'total_received': len(readings_data),
        'accepted': len(to_insert),
        'duplicates_ignored': existing_in_db + internal_batch_duplicates,
        'rejected': len(rejections),
        'duration_ms': int((time.perf_counter() - start_time) * 1000),
        'rejection_details': rejections
    }

def process_csv_reading_file(file_obj, user=None, datasource=None) -> dict:
    """
    Parses a CSV file containing 15-minute readings and delegates to bulk ingestion.
    """
    decoded = file_obj.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    readings = []
    for row in reader:
        readings.append(row)
    return ingest_bulk_readings(readings, datasource=datasource, user=user, source_type='csv_upload')
