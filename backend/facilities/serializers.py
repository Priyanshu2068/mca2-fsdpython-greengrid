"""
GreenGrid Facilities Serializers.
"""

from rest_framework import serializers
from facilities.models import Facility, Building, Meter, DataSource

class FacilitySerializer(serializers.ModelSerializer):
    meters_count = serializers.IntegerField(source='meters.count', read_only=True)
    buildings_count = serializers.IntegerField(source='buildings.count', read_only=True)

    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'code', 'facility_type', 'gross_floor_area_sqm',
            'operating_hours_per_week', 'address', 'city', 'state', 'pin_code',
            'latitude', 'longitude', 'sanctioned_demand_kva', 'meters_count',
            'buildings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'meters_count', 'buildings_count', 'created_at', 'updated_at']

class BuildingSerializer(serializers.ModelSerializer):
    facility_id = serializers.PrimaryKeyRelatedField(read_only=True, source='facility')

    class Meta:
        model = Building
        fields = ['id', 'facility_id', 'name', 'code', 'total_floors', 'floor_area_sqm', 'created_at']
        read_only_fields = ['id', 'facility_id', 'created_at']

class MeterSerializer(serializers.ModelSerializer):
    facility_id = serializers.PrimaryKeyRelatedField(read_only=True, source='facility')
    building_name = serializers.CharField(source='building.name', read_only=True, default=None)

    class Meta:
        model = Meter
        fields = [
            'id', 'facility_id', 'building', 'building_name', 'meter_identifier',
            'name', 'energy_source', 'load_category', 'meter_make', 'meter_model',
            'ct_ratio', 'pt_ratio', 'physical_location', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'facility_id', 'building_name', 'created_at', 'updated_at']

class DataSourceSerializer(serializers.ModelSerializer):
    facility_id = serializers.PrimaryKeyRelatedField(read_only=True, source='facility')

    class Meta:
        model = DataSource
        fields = [
            'id', 'facility_id', 'name', 'key_prefix', 'is_active',
            'last_used_at', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'facility_id', 'key_prefix', 'last_used_at', 'created_at']

class DataSourceCreateResponseSerializer(serializers.Serializer):
    datasource = DataSourceSerializer()
    api_key = serializers.CharField(help_text="Full plaintext API Key. Displayed ONLY ONCE.")
