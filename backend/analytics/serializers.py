"""
GreenGrid Analytics Serializers.
"""

from rest_framework import serializers
from analytics.models import HourlyRollup, DailyRollup, AnomalyAlert

class HourlyRollupSerializer(serializers.ModelSerializer):
    meter_identifier = serializers.CharField(source='meter.meter_identifier', read_only=True)
    facility_name = serializers.CharField(source='meter.facility.name', read_only=True)

    class Meta:
        model = HourlyRollup
        fields = [
            'id', 'meter_id', 'meter_identifier', 'facility_name', 'bucket_start',
            'total_energy_kwh', 'peak_demand_kw', 'min_demand_kw', 'avg_power_factor',
            'reading_count', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class DailyRollupSerializer(serializers.ModelSerializer):
    meter_identifier = serializers.CharField(source='meter.meter_identifier', read_only=True)
    facility_name = serializers.CharField(source='meter.facility.name', read_only=True)

    class Meta:
        model = DailyRollup
        fields = [
            'id', 'meter_id', 'meter_identifier', 'facility_name', 'rollup_date',
            'total_energy_kwh', 'peak_demand_kw', 'peak_timestamp',
            'off_peak_energy_kwh', 'peak_energy_kwh', 'avg_power_factor',
            'reading_count', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class AnomalyAlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    meter_identifier = serializers.CharField(source='meter.meter_identifier', read_only=True)

    class Meta:
        model = AnomalyAlert
        fields = [
            'id', 'facility_id', 'facility_name', 'meter_id', 'meter_identifier',
            'detected_at', 'anomaly_type', 'severity', 'reason',
            'baseline_value', 'observed_value', 'deviation_factor',
            'status', 'resolved_at', 'resolution_notes'
        ]
        read_only_fields = [
            'id', 'facility_id', 'facility_name', 'meter_id', 'meter_identifier',
            'detected_at', 'anomaly_type', 'severity', 'reason',
            'baseline_value', 'observed_value', 'deviation_factor', 'resolved_at'
        ]

class AnomalyAlertUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyAlert
        fields = ['status', 'resolution_notes']

