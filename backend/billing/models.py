"""
GreenGrid Billing Models.
Utility DISCOM providers, commercial tariffs, utility bills, and reconciliation.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

class UtilityProvider(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    state = models.CharField(max_length=100)
    website = models.CharField(max_length=255, blank=True, default='')
    customer_care_phone = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        db_table = 'billing_utilityprovider'
        verbose_name = 'Utility Provider'
        verbose_name_plural = 'Utility Providers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class TariffStructure(models.Model):
    provider = models.ForeignKey(
        UtilityProvider,
        on_delete=models.CASCADE,
        related_name='tariffs'
    )
    tariff_code = models.CharField(max_length=50, unique=True, db_index=True)
    tariff_name = models.CharField(max_length=255)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    base_energy_rate_inr = models.DecimalField(max_digits=10, decimal_places=4)
    peak_hour_rate_inr = models.DecimalField(max_digits=10, decimal_places=4)
    off_peak_rate_inr = models.DecimalField(max_digits=10, decimal_places=4)
    demand_charge_inr_per_kva = models.DecimalField(max_digits=10, decimal_places=2)
    pf_penalty_threshold = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal('0.900'))
    pf_penalty_rate_inr = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.5000'))
    fixed_charge_monthly_inr = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'billing_tariffstructure'
        verbose_name = 'Tariff Structure'
        verbose_name_plural = 'Tariff Structures'
        ordering = ['tariff_code']

    def __str__(self):
        return f"{self.tariff_name} [{self.tariff_code}]"

class UtilityBill(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
    ]

    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='utility_bills'
    )
    tariff = models.ForeignKey(
        TariffStructure,
        on_delete=models.PROTECT,
        related_name='bills'
    )
    bill_number = models.CharField(max_length=100, unique=True, db_index=True)
    billing_cycle_start = models.DateField()
    billing_cycle_end = models.DateField()
    due_date = models.DateField()
    billed_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    billed_max_demand_kva = models.DecimalField(max_digits=10, decimal_places=2)
    billed_amount_inr = models.DecimalField(max_digits=14, decimal_places=2)
    effective_cost_per_kwh_inr = models.DecimalField(max_digits=10, decimal_places=4)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'billing_utilitybill'
        verbose_name = 'Utility Bill'
        verbose_name_plural = 'Utility Bills'
        ordering = ['-billing_cycle_start']

    def __str__(self):
        return f"Bill {self.bill_number} - {self.facility.code} (₹{self.billed_amount_inr})"

class BillReconciliation(models.Model):
    STATUS_CHOICES = [
        ('verified_within_tolerance', 'Verified Within Tolerance (<=1.0%)'),
        ('variance_minor', 'Minor Variance (1.0% - 2.5%)'),
        ('variance_action_required', 'Action Required (>2.5%)'),
    ]

    bill = models.OneToOneField(
        UtilityBill,
        on_delete=models.CASCADE,
        related_name='reconciliation'
    )
    metered_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    discrepancy_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    discrepancy_percentage = models.DecimalField(max_digits=6, decimal_places=2)
    variance_cost_inr = models.DecimalField(max_digits=14, decimal_places=2)
    reconciliation_status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    reconciled_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'billing_billreconciliation'
        verbose_name = 'Bill Reconciliation'
        verbose_name_plural = 'Bill Reconciliations'
        ordering = ['-reconciled_at']

    def __str__(self):
        return f"Reconciliation for Bill {self.bill.bill_number}: {self.discrepancy_percentage}% variance ({self.reconciliation_status})"
