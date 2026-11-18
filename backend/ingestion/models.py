"""
GreenGrid Ingestion Models.
Raw telemetry readings and ingestion batch logs.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class BatchLog(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('api_bulk', 'Bulk Ingestion API (X-API-Key)'),
        ('csv_upload', 'Field CSV Upload'),
        ('simulator', 'Environmental Simulator Replay'),
        ('manual', 'Manual Entry'),
    ]

    datasource = models.ForeignKey(
        'facilities.DataSource',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batch_logs'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ingestion_batches'
    )
    batch_reference = models.CharField(max_length=100, unique=True, db_index=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES, default='api_bulk')
    total_records = models.PositiveIntegerField(default=0)
    accepted_records = models.PositiveIntegerField(default=0)
    duplicate_records = models.PositiveIntegerField(default=0)
    rejected_records = models.PositiveIntegerField(default=0)
    ingestion_duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    error_summary = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'ingestion_batchlog'
        verbose_name = 'Batch Log'
        verbose_name_plural = 'Batch Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_reference} ({self.source_type}): {self.accepted_records}/{self.total_records} accepted"

class RawReading(models.Model):
    meter = models.ForeignKey(
        'facilities.Meter',
        on_delete=models.CASCADE,
        related_name='raw_readings'
    )
    batch = models.ForeignKey(
        BatchLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='readings'
    )
    timestamp = models.DateTimeField(db_index=True)
    energy_kwh = models.DecimalField(max_digits=14, decimal_places=4)
    active_power_kw = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    reactive_power_kvar = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    apparent_power_kva = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'))
    voltage_v = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('415.00'))
    current_a = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    power_factor = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal('1.000'))
    frequency_hz = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ingestion_rawreading'
        verbose_name = 'Raw Reading'
        verbose_name_plural = 'Raw Readings'
        constraints = [
            models.UniqueConstraint(fields=['meter', 'timestamp'], name='uq_meter_timestamp')
        ]
        indexes = [
            models.Index(fields=['meter', '-timestamp'], name='idx_rawreading_meter_time')
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.meter.meter_identifier}: {self.energy_kwh} kWh"
