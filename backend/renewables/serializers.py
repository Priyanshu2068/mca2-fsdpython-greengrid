"""
GreenGrid Renewables Serializers.
"""

from rest_framework import serializers
from renewables.models import (
    SolarAsset,
    SolarGenerationReading,
    GridEvent,
    CarbonEmissionFactor,
)

class SolarAssetSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    facility_code = serializers.CharField(source='facility.code', read_only=True)

    class Meta:
        model = SolarAsset
        fields = [
            'id', 'facility', 'facility_name', 'facility_code',
            'array_identifier', 'name', 'rated_capacity_kwp',
            'panel_technology', 'inverter_model',
            'tilt_degrees', 'azimuth_degrees', 'commissioned_date',
            'is_active'
        ]

class SolarGenerationReadingSerializer(serializers.ModelSerializer):
    asset_identifier = serializers.CharField(source='asset.array_identifier', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = SolarGenerationReading
        fields = [
            'id', 'asset', 'asset_identifier', 'asset_name',
            'timestamp', 'generation_kwh', 'solar_irradiance_wm2',
            'ambient_temp_celsius', 'performance_ratio', 'created_at'
        ]

class GridEventSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    facility_code = serializers.CharField(source='facility.code', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = GridEvent
        fields = [
            'id', 'facility', 'facility_name', 'facility_code',
            'event_type', 'event_type_display',
            'start_time', 'end_time', 'duration_minutes',
            'fuel_consumed_litres', 'grid_restored', 'notes'
        ]

class CarbonEmissionFactorSerializer(serializers.ModelSerializer):
    energy_source_display = serializers.CharField(source='get_energy_source_display', read_only=True)

    class Meta:
        model = CarbonEmissionFactor
        fields = [
            'id', 'energy_source', 'energy_source_display',
            'co2_kg_per_kwh', 'source_reference'
        ]

class SelfConsumptionResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    total_solar_generation_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    grid_consumption_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    total_facility_consumption_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    self_consumption_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    solar_fraction_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    estimated_cost_avoided_inr = serializers.DecimalField(max_digits=14, decimal_places=2)

class SourceEmissionsItemSerializer(serializers.Serializer):
    energy_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    factor_kg_per_kwh = serializers.DecimalField(max_digits=8, decimal_places=4)
    emissions_kg_co2 = serializers.DecimalField(max_digits=14, decimal_places=2)

class CarbonEmissionsResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    breakdown_by_source = serializers.DictField(child=SourceEmissionsItemSerializer())
    total_emissions_kg_co2 = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_emissions_tco2e = serializers.DecimalField(max_digits=10, decimal_places=3)
    avoided_emissions_kg_co2 = serializers.DecimalField(max_digits=14, decimal_places=2)
    avoided_emissions_tco2e = serializers.DecimalField(max_digits=10, decimal_places=3)

