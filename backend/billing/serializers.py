"""
GreenGrid Billing Serializers.
"""

from rest_framework import serializers
from billing.models import UtilityProvider, TariffStructure, UtilityBill, BillReconciliation

class UtilityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityProvider
        fields = ['id', 'name', 'code', 'state', 'website', 'customer_care_phone']

class TariffStructureSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = TariffStructure
        fields = [
            'id', 'provider', 'provider_name', 'tariff_code', 'tariff_name',
            'effective_from', 'effective_to', 'base_energy_rate_inr',
            'peak_hour_rate_inr', 'off_peak_rate_inr', 'demand_charge_inr_per_kva',
            'pf_penalty_threshold', 'pf_penalty_rate_inr', 'fixed_charge_monthly_inr'
        ]

class UtilityBillSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    tariff_name = serializers.CharField(source='tariff.tariff_name', read_only=True)

    class Meta:
        model = UtilityBill
        fields = [
            'id', 'facility', 'facility_name', 'tariff', 'tariff_name',
            'bill_number', 'billing_cycle_start', 'billing_cycle_end', 'due_date',
            'billed_kwh', 'billed_max_demand_kva', 'billed_amount_inr',
            'effective_cost_per_kwh_inr', 'payment_status', 'created_at'
        ]
        read_only_fields = ['id', 'effective_cost_per_kwh_inr', 'created_at']

class UtilityBillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityBill
        fields = [
            'facility', 'tariff', 'bill_number', 'billing_cycle_start',
            'billing_cycle_end', 'due_date', 'billed_kwh',
            'billed_max_demand_kva', 'billed_amount_inr', 'payment_status'
        ]

class BillReconciliationSerializer(serializers.ModelSerializer):
    bill_number = serializers.CharField(source='bill.bill_number', read_only=True)
    facility_name = serializers.CharField(source='bill.facility.name', read_only=True)
    billed_kwh = serializers.DecimalField(source='bill.billed_kwh', max_digits=14, decimal_places=4, read_only=True)
    billed_amount_inr = serializers.DecimalField(source='bill.billed_amount_inr', max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = BillReconciliation
        fields = [
            'id', 'bill', 'bill_number', 'facility_name', 'billed_kwh',
            'billed_amount_inr', 'metered_kwh', 'discrepancy_kwh',
            'discrepancy_percentage', 'variance_cost_inr', 'reconciliation_status',
            'reconciled_at', 'notes'
        ]
        read_only_fields = fields
