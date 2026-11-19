"""
GreenGrid Renewables Models.
Solar PV assets, generation telemetry, grid outage logs, and CEA carbon factors.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

class SolarAsset(models.Model):
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='solar_assets'
    )
    array_identifier = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    rated_capacity_kwp = models.DecimalField(max_digits=10, decimal_places=2)
    panel_technology = models.CharField(max_length=100, default='Monocrystalline Silicon')
    inverter_model = models.CharField(max_length=100, default='Sungrow SG110CX')
    tilt_degrees = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('15.0'))
    azimuth_degrees = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('180.0'))
    commissioned_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'renewables_solarasset'
        verbose_name = 'Solar PV Asset'
        verbose_name_plural = 'Solar PV Assets'
        ordering = ['facility', 'array_identifier']

    def __str__(self):
        return f"{self.facility.name} - {self.name} ({self.rated_capacity_kwp} kWp)"

class SolarGenerationReading(models.Model):
    asset = models.ForeignKey(
        SolarAsset,
        on_delete=models.CASCADE,
        related_name='generation_readings'
    )
    timestamp = models.DateTimeField(db_index=True)
    generation_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    solar_irradiance_wm2 = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    ambient_temp_celsius = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('25.00'))
    performance_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.80'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'renewables_solargenerationreading'
        verbose_name = 'Solar Generation Reading'
        verbose_name_plural = 'Solar Generation Readings'
        constraints = [
            models.UniqueConstraint(fields=['asset', 'timestamp'], name='uq_asset_timestamp')
        ]
        indexes = [
            models.Index(fields=['asset', '-timestamp'], name='idx_solargen_asset_time'),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.asset.array_identifier}: {self.generation_kwh} kWh (PR {self.performance_ratio})"

class GridEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('grid_outage', 'Complete Grid Outage'),
        ('voltage_sag', 'Transient Voltage Sag'),
        ('frequency_aberration', 'Grid Frequency Aberration'),
        ('dg_cut_in', 'Diesel Generator Cut-In'),
        ('dg_cut_out', 'Diesel Generator Cut-Out'),
    ]

    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='grid_events'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fuel_consumed_litres = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grid_restored = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'renewables_gridevent'
        verbose_name = 'Grid Event & Outage Log'
        verbose_name_plural = 'Grid Events & Outage Logs'
        indexes = [
            models.Index(fields=['facility', '-start_time'], name='idx_gridevent_fac_time'),
        ]
        ordering = ['-start_time']

    def __str__(self):
        return f"[{self.start_time}] {self.facility.name}: {self.get_event_type_display()} ({self.duration_minutes} min)"

class CarbonEmissionFactor(models.Model):
    ENERGY_SOURCE_CHOICES = [
        ('grid', 'State Grid Supply (CEA Baseline)'),
        ('diesel_generator', 'Captive Diesel Generator'),
        ('solar', 'On-Site Solar PV Generation'),
        ('natural_gas', 'Natural Gas Piped Supply'),
    ]

    energy_source = models.CharField(max_length=50, choices=ENERGY_SOURCE_CHOICES, unique=True)
    co2_kg_per_kwh = models.DecimalField(max_digits=8, decimal_places=4)
    source_reference = models.CharField(
        max_length=255,
        default='Central Electricity Authority (CEA) India Baseline CO2 Database Version 19'
    )

    class Meta:
        db_table = 'renewables_carbonemissionfactor'
        verbose_name = 'Carbon Emission Factor'
        verbose_name_plural = 'Carbon Emission Factors'

    def __str__(self):
        return f"{self.get_energy_source_display()}: {self.co2_kg_per_kwh} kg CO2/kWh"

