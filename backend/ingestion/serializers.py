"""
GreenGrid Ingestion Serializers.
"""

from rest_framework import serializers
from ingestion.models import RawReading, BatchLog

class ReadingItemSerializer(serializers.Serializer):
    meter_identifier = serializers.CharField(required=True)
    timestamp = serializers.DateTimeField(required=True)
    energy_kwh = serializers.DecimalField(max_digits=14, decimal_places=4, required=True, min_value=0)
    active_power_kw = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=0)
    reactive_power_kvar = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=0)
    apparent_power_kva = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=0)
    voltage_v = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=415.00, min_value=0)
    current_a = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.00, min_value=0)
    power_factor = serializers.DecimalField(max_digits=4, decimal_places=3, required=False, default=1.000, min_value=0, max_value=1)
    frequency_hz = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=50.00)

class BulkIngestionRequestSerializer(serializers.Serializer):
    readings = ReadingItemSerializer(many=True, required=True)

class BulkIngestionResponseSerializer(serializers.Serializer):
    batch_reference = serializers.CharField()
    status = serializers.CharField()
    total_received = serializers.IntegerField()
    accepted = serializers.IntegerField()
    duplicates_ignored = serializers.IntegerField()
    rejected = serializers.IntegerField()
    duration_ms = serializers.IntegerField()
    rejection_details = serializers.ListField(child=serializers.DictField())

class RawReadingSerializer(serializers.ModelSerializer):
    meter_identifier = serializers.CharField(source='meter.meter_identifier', read_only=True)
    facility_name = serializers.CharField(source='meter.facility.name', read_only=True)
    load_category = serializers.CharField(source='meter.load_category', read_only=True)

    class Meta:
        model = RawReading
        fields = [
            'id', 'meter_id', 'meter_identifier', 'facility_name', 'load_category',
            'timestamp', 'energy_kwh', 'active_power_kw', 'reactive_power_kvar',
            'apparent_power_kva', 'voltage_v', 'current_a', 'power_factor',
            'frequency_hz', 'created_at'
        ]
        read_only_fields = fields

class BatchLogSerializer(serializers.ModelSerializer):
    datasource_name = serializers.CharField(source='datasource.name', read_only=True, default=None)

    class Meta:
        model = BatchLog
        fields = [
            'id', 'batch_reference', 'source_type', 'datasource_name',
            'total_records', 'accepted_records', 'duplicate_records',
            'rejected_records', 'ingestion_duration_ms', 'created_at', 'error_summary'
        ]
        read_only_fields = fields

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
