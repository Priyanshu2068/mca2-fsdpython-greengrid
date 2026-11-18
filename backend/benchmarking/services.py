"""
GreenGrid Benchmarking Services (EUI Scoring & National Distribution).
"""

from decimal import Decimal
from datetime import date
from django.utils import timezone
from django.db.models import Sum
from facilities.models import Facility
from analytics.models import DailyRollup
from benchmarking.models import BuildingBenchmark, FacilityBenchmarkScore

def calculate_and_save_facility_benchmark(facility: Facility, year: int) -> FacilityBenchmarkScore:
    """
    Computes annual Energy Use Intensity (EUI in kWh/m2/year) and assigns BEE Star Rating (1-5).
    """
    incomer_meter_ids = list(
        facility.meters.filter(is_active=True, load_category='main_incomer', energy_source='grid')
        .values_list('id', flat=True)
    ) or list(facility.meters.filter(is_active=True).values_list('id', flat=True))

    annual_kwh = (
        DailyRollup.objects.filter(
            meter_id__in=incomer_meter_ids,
            rollup_date__year=year
        ).aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0.0000')
    )

    # If rollups exist for only part of the year, extrapolate to full 365 days
    days_recorded = (
        DailyRollup.objects.filter(meter_id__in=incomer_meter_ids, rollup_date__year=year)
        .values('rollup_date').distinct().count()
    )
    if 0 < days_recorded < 365:
        annual_kwh = round((annual_kwh / Decimal(str(days_recorded))) * Decimal('365.0'), 4)
    elif days_recorded == 0:
        # Default baseline if zero rollups exist
        annual_kwh = facility.gross_floor_area_sqm * Decimal('175.00')

    gfa = facility.gross_floor_area_sqm or Decimal('1000.00')
    calculated_eui = round(annual_kwh / gfa, 2)

    # Fetch benchmark standard for facility type
    benchmark = BuildingBenchmark.objects.filter(facility_type=facility.facility_type).first()
    if benchmark:
        top_20 = benchmark.top_20_percentile_eui
        median = benchmark.median_eui_kwh_sqm_year
        bottom_20 = benchmark.bottom_20_percentile_eui
    else:
        top_20 = Decimal('140.00')
        median = Decimal('185.00')
        bottom_20 = Decimal('235.00')

    # Star rating evaluation (lower EUI = higher efficiency)
    band_4 = round((top_20 + median) / Decimal('2.0'), 2)
    band_2 = round((median + bottom_20) / Decimal('2.0'), 2)

    if calculated_eui <= top_20:
        stars = 5
        percentile = Decimal('90.00')
    elif calculated_eui <= band_4:
        stars = 4
        percentile = Decimal('78.00')
    elif calculated_eui <= median:
        stars = 3
        percentile = Decimal('55.00')
    elif calculated_eui <= band_2:
        stars = 2
        percentile = Decimal('35.00')
    else:
        stars = 1
        percentile = Decimal('15.00')

    score, _ = FacilityBenchmarkScore.objects.update_or_create(
        facility=facility,
        year=year,
        defaults={
            'annual_energy_kwh': annual_kwh,
            'calculated_eui_kwh_sqm_year': calculated_eui,
            'national_percentile': percentile,
            'star_rating': stars,
            'computed_at': timezone.now()
        }
    )
    return score

def compute_all_facility_benchmarks(year: int) -> int:
    facilities = Facility.objects.all()
    count = 0
    for fac in facilities:
        calculate_and_save_facility_benchmark(fac, year)
        count += 1
    return count

