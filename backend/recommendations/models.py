"""
GreenGrid Recommendations Models.
Deterministic Energy Conservation Measures (ECMs) with actionable steps and INR savings.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

class ECMRule(models.Model):
    CATEGORY_CHOICES = [
        ('peak_shaving', 'Peak Demand Shaving'),
        ('power_factor_correction', 'Power Factor Correction (APFC)'),
        ('hvac_scheduling', 'HVAC & Chiller Scheduling'),
        ('baseload_reduction', 'Baseload Leakage Reduction'),
        ('dg_displacement', 'Diesel Generator Displacement'),
    ]

    rule_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TEXTField() if hasattr(models, 'TEXTField') else models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'recommendations_ecmrule'
        verbose_name = 'ECM Rule Definition'
        verbose_name_plural = 'ECM Rule Definitions'

    def __str__(self):
        return f"[{self.rule_code}] {self.name}"

class Recommendation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active Opportunity'),
        ('accepted', 'Accepted by Customer'),
        ('dismissed', 'Dismissed by Customer'),
        ('implemented', 'Implemented On-Site'),
    ]

    rule = models.ForeignKey(
        ECMRule,
        on_delete=models.RESTRICT,
        related_name='recommendations'
    )
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    meter = models.ForeignKey(
        'facilities.Meter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    action_plan = models.TextField()
    estimated_annual_kwh_savings = models.DecimalField(max_digits=14, decimal_places=4)
    estimated_annual_savings_inr = models.DecimalField(max_digits=14, decimal_places=2)
    implementation_cost_inr = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    estimated_payback_months = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    dismissal_reason = models.TextField(blank=True, default='')
    generated_at = models.DateTimeField(default=timezone.now)
    actioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'recommendations_recommendation'
        verbose_name = 'Energy Conservation Recommendation'
        verbose_name_plural = 'Energy Conservation Recommendations'
        indexes = [
            models.Index(fields=['facility', 'status'], name='idx_recom_fac_status'),
            models.Index(fields=['rule', 'facility'], name='idx_recom_rule_fac'),
        ]
        ordering = ['-generated_at', '-estimated_annual_savings_inr']

    def __str__(self):
        return f"{self.facility.name} - {self.title} (₹{self.estimated_annual_savings_inr}/yr)"
