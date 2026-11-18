"""
GreenGrid Analytics Models.
Hourly & daily pre-aggregated rollups, plus Anomaly Alert records.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

class HourlyRollup(models.Model):
    meter = models.ForeignKey(
        'facilities.Meter',
        on_delete=models.CASCADE,
        related_name='hourly_rollups'
    )
    bucket_start = models.DateTimeField(db_index=True)
    total_energy_kwh = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal('0.0000'))
    peak_demand_kw = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    min_demand_kw = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    avg_power_factor = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal('1.000'))
    reading_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_hourlyrollup'
        verbose_name = 'Hourly Rollup'
        verbose_name_plural = 'Hourly Rollups'
        constraints = [
            models.UniqueConstraint(fields=['meter', 'bucket_start'], name='uq_hourly_meter_bucket')
        ]
        indexes = [
            models.Index(fields=['meter', '-bucket_start'], name='idx_hourly_meter_time')
        ]
        ordering = ['-bucket_start']

    def __str__(self):
        return f"[{self.bucket_start}] {self.meter.meter_identifier}: {self.total_energy_kwh} kWh (peak {self.peak_demand_kw} kW)"

class DailyRollup(models.Model):
    meter = models.ForeignKey(
        'facilities.Meter',
        on_delete=models.CASCADE,
        related_name='daily_rollups'
    )
    rollup_date = models.DateField(db_index=True)
    total_energy_kwh = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal('0.0000'))
    peak_demand_kw = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    peak_timestamp = models.DateTimeField(null=True, blank=True)
    off_peak_energy_kwh = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal('0.0000'))
    peak_energy_kwh = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal('0.0000'))
    avg_power_factor = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal('1.000'))
    reading_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_dailyrollup'
        verbose_name = 'Daily Rollup'
        verbose_name_plural = 'Daily Rollups'
        constraints = [
            models.UniqueConstraint(fields=['meter', 'rollup_date'], name='uq_daily_meter_date')
        ]
        indexes = [
            models.Index(fields=['meter', '-rollup_date'], name='idx_daily_meter_date')
        ]
        ordering = ['-rollup_date']

    def __str__(self):
        return f"[{self.rollup_date}] {self.meter.meter_identifier}: {self.total_energy_kwh} kWh (peak {self.peak_demand_kw} kW)"

class AnomalyAlert(models.Model):
    ANOMALY_TYPE_CHOICES = [
        ('consumption_spike', 'Consumption Spike (>1.3x 4-Week Median)'),
        ('low_power_factor', 'Degraded Power Factor (< 0.900)'),
        ('dg_grid_clash', 'DG Operation during Grid Active'),
        ('meter_silent', 'Meter Communication Timeout (> 2 Hours)'),
        ('demand_limit_breach', 'Sanctioned Demand Breach (>90% kVA)'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]

    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='anomaly_alerts'
    )
    meter = models.ForeignKey(
        'facilities.Meter',
        on_delete=models.CASCADE,
        related_name='anomaly_alerts'
    )
    detected_at = models.DateTimeField(default=timezone.now, db_index=True)
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    reason = models.TextField()
    baseline_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    observed_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    deviation_factor = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open', db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'analytics_anomalyalert'
        verbose_name = 'Anomaly Alert'
        verbose_name_plural = 'Anomaly Alerts'
        ordering = ['-detected_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.meter.meter_identifier} - {self.anomaly_type} ({self.status})"

