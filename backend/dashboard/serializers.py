"""
GreenGrid Dashboard Serializers.
"""

from rest_framework import serializers

class MetricSummarySerializer(serializers.Serializer):
    today_consumption_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    yesterday_same_time_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    change_percentage = serializers.DecimalField(max_digits=6, decimal_places=2)
    month_to_date_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    current_peak_demand_kw = serializers.DecimalField(max_digits=12, decimal_places=4)
    sanctioned_demand_kva = serializers.DecimalField(max_digits=10, decimal_places=2)
    demand_utilization_pct = serializers.DecimalField(max_digits=6, decimal_places=2)
    active_anomalies_count = serializers.IntegerField()

class KPISummaryResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    as_of = serializers.DateTimeField()
    latest_data_at = serializers.DateTimeField(allow_null=True)
    metrics = MetricSummarySerializer()

class TrendPointSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(required=False)
    date = serializers.DateField(required=False)
    energy_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    peak_demand_kw = serializers.DecimalField(max_digits=12, decimal_places=4)

class TrendResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    range = serializers.CharField()
    points = TrendPointSerializer(many=True)

class EnergyMixItemSerializer(serializers.Serializer):
    source = serializers.CharField()
    energy_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2)

class EnergyMixResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    total_consumption_kwh = serializers.DecimalField(max_digits=16, decimal_places=4)
    energy_mix = EnergyMixItemSerializer(many=True)

class LoadBreakdownItemSerializer(serializers.Serializer):
    load_category = serializers.CharField()
    energy_kwh = serializers.DecimalField(max_digits=14, decimal_places=4)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2)

class LoadBreakdownResponseSerializer(serializers.Serializer):
    facility_id = serializers.IntegerField()
    facility_name = serializers.CharField()
    total_submetered_kwh = serializers.DecimalField(max_digits=16, decimal_places=4)
    breakdown = LoadBreakdownItemSerializer(many=True)
