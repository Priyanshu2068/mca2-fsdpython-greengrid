"""
GreenGrid Benchmarking Models.
Building type standards (BEE Star Ratings) and facility annual EUI scores.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

class BuildingBenchmark(models.Model):
    FACILITY_TYPE_CHOICES = [
        ('commercial_office', 'Commercial Office'),
        ('tech_park', 'Technology Park'),
        ('hospital', 'Hospital & Healthcare'),
        ('retail_mall', 'Retail Mall'),
        ('hotel', 'Hospitality & Hotel'),
        ('educational_campus', 'Educational Campus'),
    ]

    facility_type = models.CharField(max_length=50, choices=FACILITY_TYPE_CHOICES, unique=True)
    median_eui_kwh_sqm_year = models.DecimalField(max_digits=8, decimal_places=2)
    top_20_percentile_eui = models.DecimalField(max_digits=8, decimal_places=2)
    bottom_20_percentile_eui = models.DecimalField(max_digits=8, decimal_places=2)
    benchmark_standard = models.CharField(max_length=150, default='BEE India Star Rating Standards 2024')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'benchmarking_buildingbenchmark'
        verbose_name = 'Building Benchmark Standard'
        verbose_name_plural = 'Building Benchmark Standards'

    def __str__(self):
        return f"{self.get_facility_type_display()} (Median EUI: {self.median_eui_kwh_sqm_year} kWh/m²/yr)"

class FacilityBenchmarkScore(models.Model):
    facility = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.CASCADE,
        related_name='benchmark_scores'
    )
    year = models.PositiveIntegerField(db_index=True)
    annual_energy_kwh = models.DecimalField(max_digits=16, decimal_places=4)
    calculated_eui_kwh_sqm_year = models.DecimalField(max_digits=8, decimal_places=2)
    national_percentile = models.DecimalField(max_digits=5, decimal_places=2)
    star_rating = models.PositiveSmallIntegerField() # 1 to 5 Stars
    computed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'benchmarking_facilitybenchmarkscore'
        verbose_name = 'Facility Benchmark Score'
        verbose_name_plural = 'Facility Benchmark Scores'
        constraints = [
            models.UniqueConstraint(fields=['facility', 'year'], name='uq_facility_benchmark_year')
        ]
        ordering = ['-year', 'calculated_eui_kwh_sqm_year']

    def __str__(self):
        return f"{self.facility.name} ({self.year}): {self.calculated_eui_kwh_sqm_year} kWh/m²/yr [{self.star_rating} Stars]"

