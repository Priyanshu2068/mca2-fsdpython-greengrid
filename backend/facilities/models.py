"""
GreenGrid Facilities Models.
Facility hierarchy: Facility -> Building -> Meter, plus User Assignments and DataSources.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class Facility(models.Model):
    FACILITY_TYPE_CHOICES = [
        ('commercial_office', 'Commercial Office'),
        ('tech_park', 'Technology Park'),
        ('hospital', 'Hospital & Healthcare'),
        ('retail_mall', 'Retail Mall'),
        ('hotel', 'Hospitality & Hotel'),
        ('educational_campus', 'Educational Campus'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    facility_type = models.CharField(max_length=50, choices=FACILITY_TYPE_CHOICES, db_index=True)
    gross_floor_area_sqm = models.DecimalField(max_digits=12, decimal_places=2)
    operating_hours_per_week = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    sanctioned_demand_kva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('500.00'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facilities_facility'
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class UserFacilityAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facility_assignments'
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'facilities_userfacilityassignment'
        unique_together = ('user', 'facility')

    def __str__(self):
        return f"{self.user.email} -> {self.facility.name}"

class Building(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    total_floors = models.PositiveIntegerField(default=1)
    floor_area_sqm = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'facilities_building'
        unique_together = ('facility', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.facility.code}]"

class Meter(models.Model):
    ENERGY_SOURCE_CHOICES = [
        ('grid', 'Utility Grid'),
        ('diesel_generator', 'Diesel Generator (DG)'),
        ('solar', 'Rooftop / Ground Solar PV'),
        ('water', 'Water Telemetry'),
        ('gas', 'Natural Gas'),
    ]

    LOAD_CATEGORY_CHOICES = [
        ('main_incomer', 'Main Incomer'),
        ('hvac', 'HVAC & Chillers'),
        ('lighting', 'Lighting Circuits'),
        ('it_infrastructure', 'IT & Server Infrastructure'),
        ('auxiliary_pumps', 'Auxiliary & Fire Pumps'),
        ('elevators', 'Elevators & Escalators'),
        ('ev_chargers', 'EV Charging Infrastructure'),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='meters')
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, related_name='meters')
    meter_identifier = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    energy_source = models.CharField(max_length=50, choices=ENERGY_SOURCE_CHOICES)
    load_category = models.CharField(max_length=50, choices=LOAD_CATEGORY_CHOICES)
    meter_make = models.CharField(max_length=100, default='Schneider Electric')
    meter_model = models.CharField(max_length=100, default='EM6400NG')
    ct_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    pt_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    physical_location = models.CharField(max_length=255, default='Main Electrical Room')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facilities_meter'
        verbose_name = 'Meter'
        verbose_name_plural = 'Meters'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.meter_identifier})"

class DataSource(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='datasources')
    name = models.CharField(max_length=150)
    key_prefix = models.CharField(max_length=16)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'facilities_datasource'
        verbose_name = 'DataSource'
        verbose_name_plural = 'DataSources'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} [{self.key_prefix}...] ({'Active' if self.is_active else 'Revoked'})"
