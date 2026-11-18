import pytest
from decimal import Decimal
from datetime import date
from django.core.management import call_command
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter, UserFacilityAssignment
from analytics.models import DailyRollup
from benchmarking.models import BuildingBenchmark, FacilityBenchmarkScore
from benchmarking.services import calculate_and_save_facility_benchmark, compute_all_facility_benchmarks

@pytest.fixture
def benchmark_setup(db):
    admin = CustomUser.objects.create_superuser(email='bench_adm@greengrid.in', password='pass')
    cust1 = CustomUser.objects.create_user(email='cust1@greengrid.in', password='pass', role='customer')
    cust2 = CustomUser.objects.create_user(email='cust2@greengrid.in', password='pass', role='customer')

    # Benchmark Standard
    standard = BuildingBenchmark.objects.create(
        facility_type='commercial_office',
        median_eui_kwh_sqm_year=Decimal('180.00'),
        top_20_percentile_eui=Decimal('130.00'),
        bottom_20_percentile_eui=Decimal('230.00'),
        benchmark_standard='BEE Star Rating Commercial Buildings 2024'
    )

    # Facility 1: Efficient Building (GFA = 10,000 sqm, low consumption -> 5 Stars)
    fac1 = Facility.objects.create(
        name='Eco Office Tower',
        code='FAC-ECO-01',
        facility_type='commercial_office',
        gross_floor_area_sqm=Decimal('10000.00'),
        address='Whitefield',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560066'
    )
    m1 = Meter.objects.create(
        facility=fac1,
        meter_identifier='MTR-ECO-01',
        name='Main Incomer Eco',
        energy_source='grid',
        load_category='main_incomer'
    )

    # Facility 2: Inefficient Building (GFA = 5,000 sqm, high consumption -> 1 Star)
    fac2 = Facility.objects.create(
        name='Vintage Complex',
        code='FAC-VIN-02',
        facility_type='commercial_office',
        gross_floor_area_sqm=Decimal('5000.00'),
        address='MG Road',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560001'
    )
    m2 = Meter.objects.create(
        facility=fac2,
        meter_identifier='MTR-VIN-02',
        name='Main Incomer Vintage',
        energy_source='grid',
        load_category='main_incomer'
    )

    # Assign fac1 to cust1
    UserFacilityAssignment.objects.create(user=cust1, facility=fac1)

    # Create daily rollups for full 365 days or sample days
    # For fac1: 100 days of 3,000 kWh -> extrapolated = (300000 / 100) * 365 = 1,095,000 kWh -> EUI = 109.5 kWh/m2/yr (<130 -> 5 stars)
    for d in range(1, 101):
        m = (d - 1) // 28 + 1
        day = (d - 1) % 28 + 1
        DailyRollup.objects.create(
            meter=m1,
            rollup_date=date(2025, m, day),
            total_energy_kwh=Decimal('3000.0000'),
            peak_energy_kwh=Decimal('1500.0000'),
            off_peak_energy_kwh=Decimal('1500.0000')
        )

    # For fac2: 100 days of 4,000 kWh -> extrapolated = 4000 * 365 = 1,460,000 kWh -> EUI = 1,460,000 / 5000 = 292 kWh/m2/yr (>205 -> 1 star)
    for d in range(1, 101):
        m = (d - 1) // 28 + 1
        day = (d - 1) % 28 + 1
        DailyRollup.objects.create(
            meter=m2,
            rollup_date=date(2025, m, day),
            total_energy_kwh=Decimal('4000.0000'),
            peak_energy_kwh=Decimal('2000.0000'),
            off_peak_energy_kwh=Decimal('2000.0000')
        )

    return {
        'admin': admin,
        'cust1': cust1,
        'cust2': cust2,
        'standard': standard,
        'fac1': fac1,
        'fac2': fac2,
        'meter1': m1,
        'meter2': m2,
    }

def test_facility_benchmark_calculation(benchmark_setup):
    fac1 = benchmark_setup['fac1']
    score1 = calculate_and_save_facility_benchmark(fac1, year=2025)

    assert score1.year == 2025
    assert score1.star_rating == 5
    assert score1.calculated_eui_kwh_sqm_year < Decimal('130.00')
    assert score1.national_percentile == Decimal('90.00')

    fac2 = benchmark_setup['fac2']
    score2 = calculate_and_save_facility_benchmark(fac2, year=2025)

    assert score2.year == 2025
    assert score2.star_rating == 1
    assert score2.calculated_eui_kwh_sqm_year > Decimal('230.00')
    assert score2.national_percentile == Decimal('15.00')

def test_compute_benchmarks_management_command(benchmark_setup):
    call_command('compute_benchmarks', year=2025)

    scores = FacilityBenchmarkScore.objects.filter(year=2025)
    assert scores.count() == 2

def test_benchmarking_api_endpoints(benchmark_setup):
    admin = benchmark_setup['admin']
    cust1 = benchmark_setup['cust1']
    call_command('compute_benchmarks', year=2025)

    client = APIClient()

    # 1. Standards endpoint
    client.force_authenticate(user=admin)
    res_std = client.get('/api/v1/benchmarking/standards/')
    assert res_std.status_code == 200
    assert len(res_std.data) == 1
    assert res_std.data[0]['facility_type'] == 'commercial_office'

    # 2. Facility Scores endpoint - Admin sees all
    res_scores_admin = client.get('/api/v1/benchmarking/scores/?year=2025')
    assert res_scores_admin.status_code == 200
    assert len(res_scores_admin.data) == 2

    # 3. Facility Scores endpoint - Customer only sees assigned facility (FAC-ECO-01)
    client.force_authenticate(user=cust1)
    res_scores_cust1 = client.get('/api/v1/benchmarking/scores/?year=2025')
    assert res_scores_cust1.status_code == 200
    assert len(res_scores_cust1.data) == 1
    assert res_scores_cust1.data[0]['facility_code'] == 'FAC-ECO-01'

    # 4. Rankings endpoint (leaderboard within category)
    res_rank = client.get('/api/v1/benchmarking/ranking/?facility_type=commercial_office&year=2025')
    assert res_rank.status_code == 200
    assert len(res_rank.data) == 2
    # Ranked ascending by EUI: Eco Tower (lower EUI) is ranked first
    assert res_rank.data[0]['facility_code'] == 'FAC-ECO-01'
    assert res_rank.data[1]['facility_code'] == 'FAC-VIN-02'

