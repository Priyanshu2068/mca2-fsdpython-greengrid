"""
GreenGrid Benchmarking Serializers.
"""

from rest_framework import serializers
from benchmarking.models import BuildingBenchmark, FacilityBenchmarkScore

class BuildingBenchmarkSerializer(serializers.ModelSerializer):
    facility_type_display = serializers.CharField(source='get_facility_type_display', read_only=True)

    class Meta:
        model = BuildingBenchmark
        fields = [
            'id', 'facility_type', 'facility_type_display',
            'median_eui_kwh_sqm_year', 'top_20_percentile_eui',
            'bottom_20_percentile_eui', 'benchmark_standard', 'updated_at'
        ]

class FacilityBenchmarkScoreSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    facility_code = serializers.CharField(source='facility.code', read_only=True)
    facility_type = serializers.CharField(source='facility.facility_type', read_only=True)
    gross_floor_area_sqm = serializers.DecimalField(source='facility.gross_floor_area_sqm', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FacilityBenchmarkScore
        fields = [
            'id', 'facility', 'facility_name', 'facility_code', 'facility_type', 'gross_floor_area_sqm',
            'year', 'annual_energy_kwh', 'calculated_eui_kwh_sqm_year',
            'national_percentile', 'star_rating', 'computed_at'
        ]
