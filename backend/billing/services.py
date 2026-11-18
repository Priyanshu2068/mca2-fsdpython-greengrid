"""
GreenGrid Billing Services (Calculation & Reconciliation Engine).
"""

from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from facilities.models import Facility
from analytics.models import DailyRollup
from billing.models import UtilityBill, BillReconciliation, TariffStructure

@transaction.atomic
def record_utility_bill(
    facility: Facility,
    tariff: TariffStructure,
    bill_number: str,
    billing_cycle_start,
    billing_cycle_end,
    due_date,
    billed_kwh: Decimal,
    billed_max_demand_kva: Decimal,
    billed_amount_inr: Decimal,
    payment_status='unpaid',
    auto_reconcile=True
) -> UtilityBill:
    if billed_kwh <= Decimal('0.0000'):
        raise ValidationError({'billed_kwh': ['Billed kWh must be strictly greater than zero.']})
    if billed_amount_inr < Decimal('0.00'):
        raise ValidationError({'billed_amount_inr': ['Billed amount cannot be negative.']})
    if billing_cycle_end < billing_cycle_start:
        raise ValidationError({'billing_cycle_end': ['Billing cycle end date cannot be earlier than start date.']})

    bill_num_clean = bill_number.strip().upper()
    if UtilityBill.objects.filter(bill_number=bill_num_clean).exists():
        raise ValidationError({'bill_number': ['A bill with this number already exists.']})

    effective_cost = round(billed_amount_inr / billed_kwh, 4)

    bill = UtilityBill.objects.create(
        facility=facility,
        tariff=tariff,
        bill_number=bill_num_clean,
        billing_cycle_start=billing_cycle_start,
        billing_cycle_end=billing_cycle_end,
        due_date=due_date,
        billed_kwh=billed_kwh,
        billed_max_demand_kva=billed_max_demand_kva,
        billed_amount_inr=billed_amount_inr,
        effective_cost_per_kwh_inr=effective_cost,
        payment_status=payment_status
    )

    if auto_reconcile:
        reconcile_utility_bill(bill)

    return bill

def reconcile_utility_bill(bill: UtilityBill) -> BillReconciliation:
    """
    Reconciles utility billed kWh against internal meter daily rollups across cycle.
    Calculates discrepancy kWh, discrepancy percentage, and financial variance in INR.
    """
    facility = bill.facility
    incomer_meters = facility.meters.filter(is_active=True, load_category='main_incomer', energy_source='grid')
    incomer_meter_ids = list(incomer_meters.values_list('id', flat=True)) or list(facility.meters.values_list('id', flat=True))

    metered_sum = (
        DailyRollup.objects.filter(
            meter_id__in=incomer_meter_ids,
            rollup_date__gte=bill.billing_cycle_start,
            rollup_date__lte=bill.billing_cycle_end
        ).aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0.0000')
    )

    discrepancy_kwh = bill.billed_kwh - metered_sum
    if bill.billed_kwh > Decimal('0.0000'):
        discrepancy_pct = round((discrepancy_kwh / bill.billed_kwh) * Decimal('100.0'), 2)
    else:
        discrepancy_pct = Decimal('0.00')

    variance_cost_inr = round(discrepancy_kwh * bill.effective_cost_per_kwh_inr, 2)

    abs_pct = abs(discrepancy_pct)
    if abs_pct <= Decimal('1.00'):
        status = 'verified_within_tolerance'
        notes = f"Verified: variance {discrepancy_pct}% is within 1.0% permissible transformer loss threshold."
    elif abs_pct <= Decimal('2.50'):
        status = 'variance_minor'
        notes = f"Minor variance of {discrepancy_pct}% (₹{variance_cost_inr}). Acceptable under utility billing margin."
    else:
        status = 'variance_action_required'
        notes = f"Significant discrepancy of {discrepancy_pct}% (₹{variance_cost_inr}) detected. Billing audit dispute recommended."

    reconciliation, _ = BillReconciliation.objects.update_or_create(
        bill=bill,
        defaults={
            'metered_kwh': metered_sum,
            'discrepancy_kwh': discrepancy_kwh,
            'discrepancy_percentage': discrepancy_pct,
            'variance_cost_inr': variance_cost_inr,
            'reconciliation_status': status,
            'reconciled_at': timezone.now(),
            'notes': notes
        }
    )
    return reconciliation
