import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter, UserFacilityAssignment
from analytics.models import DailyRollup
from renewables.models import (
    SolarAsset,
    SolarGenerationReading,
    GridEvent,
    CarbonEmissionFactor,
)
from renewables.services import (
    record_solar_generation_reading,
    calculate_solar_self_consumption,
    calculate_carbon_emissions,
    record_grid_event,
    ensure_default_emission_factors,
)

@pytest.fixture
def renewables_setup(db):
    admin = CustomUser.objects.create_superuser(email='ren_adm@greengrid.in', password='pass')
    cust1 = CustomUser.objects.create_user(email='ren_cust1@greengrid.in', password='pass', role='customer')
    cust2 = CustomUser.objects.create_user(email='ren_cust2@greengrid.in', password='pass', role='customer')

    # Facility 1: Solar Enabled Facility
    fac1 = Facility.objects.create(
        name='Green Horizon Campus',
        code='FAC-GHC-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('30000.00'),
        address='Outer Ring Road',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560103'
    )
    incomer = Meter.objects.create(
        facility=fac1,
        meter_identifier='MTR-GHC-INC',
        name='Main Grid Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    dg_meter = Meter.objects.create(
        facility=fac1,
        meter_identifier='MTR-GHC-DG',
        name='Backup DG Set',
        energy_source='diesel_generator',
        load_category='backup_generation'
    )

    # Facility 2: Unassigned Facility
    fac2 = Facility.objects.create(
        name='Solitaire Mall',
        code='FAC-SOL-02',
        facility_type='retail_mall',
        gross_floor_area_sqm=Decimal('12000.00'),
        address='Indiranagar',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560038'
    )

    # Assign fac1 to cust1, fac2 to cust2
    UserFacilityAssignment.objects.create(user=cust1, facility=fac1)
    UserFacilityAssignment.objects.create(user=cust2, facility=fac2)

    # Solar Asset at fac1: 100 kWp rooftop solar
    solar_asset = SolarAsset.objects.create(
        facility=fac1,
        array_identifier='PV-ROOF-100KW',
        name='Rooftop Monocrystalline Array',
        rated_capacity_kwp=Decimal('100.00'),
        panel_technology='Monocrystalline Silicon',
        inverter_model='Sungrow SG110CX',
        tilt_degrees=Decimal('15.0'),
        azimuth_degrees=Decimal('180.0'),
        commissioned_date=date(2024, 1, 15)
    )

    # Populate rollups for Grid and DG for March 2026
    # 10 days of Grid: 1,000 kWh/day = 10,000 kWh
    for day in range(1, 11):
        DailyRollup.objects.create(
            meter=incomer,
            rollup_date=date(2026, 3, day),
            total_energy_kwh=Decimal('1000.0000'),
            peak_energy_kwh=Decimal('500.0000'),
            off_peak_energy_kwh=Decimal('500.0000')
        )
    # 2 days of DG: 200 kWh/day = 400 kWh
    for day in (3, 7):
        DailyRollup.objects.create(
            meter=dg_meter,
            rollup_date=date(2026, 3, day),
            total_energy_kwh=Decimal('200.0000'),
            peak_energy_kwh=Decimal('100.0000'),
            off_peak_energy_kwh=Decimal('100.0000')
        )

    return {
        'admin': admin,
        'cust1': cust1,
        'cust2': cust2,
        'fac1': fac1,
        'fac2': fac2,
        'solar_asset': solar_asset,
        'incomer': incomer,
    }

def test_record_solar_generation_and_pr_calculation(renewables_setup):
    asset = renewables_setup['solar_asset']
    ts = timezone.now()

    # 100 kWp array with 800 W/m2 irradiance for 15 mins
    # Expected kWh = 100 * (800 / 1000) * 0.25 = 20 kWh
    # If generated = 16 kWh -> PR = 16 / 20 = 0.80
    reading = record_solar_generation_reading(
        asset=asset,
        timestamp=ts,
        generation_kwh=Decimal('16.0000'),
        solar_irradiance_wm2=Decimal('800.00'),
        ambient_temp_celsius=Decimal('30.00')
    )

    assert reading.generation_kwh == Decimal('16.0000')
    assert reading.performance_ratio == Decimal('0.80')

    # Idempotent update on same timestamp
    updated = record_solar_generation_reading(
        asset=asset,
        timestamp=ts,
        generation_kwh=Decimal('17.0000'),
        solar_irradiance_wm2=Decimal('800.00'),
        ambient_temp_celsius=Decimal('31.00')
    )
    assert updated.id == reading.id
    assert updated.generation_kwh == Decimal('17.0000')
    assert SolarGenerationReading.objects.count() == 1

def test_solar_self_consumption_calculation(renewables_setup):
    fac1 = renewables_setup['fac1']
    asset = renewables_setup['solar_asset']

    # Record 1000 kWh of solar generation across March 1-10
    base_time = timezone.make_aware(datetime(2026, 3, 1, 12, 0))
    for i in range(10):
        t = base_time + timedelta(days=i)
        record_solar_generation_reading(
            asset=asset,
            timestamp=t,
            generation_kwh=Decimal('100.0000'),
            solar_irradiance_wm2=Decimal('600.00')
        )

    res = calculate_solar_self_consumption(
        facility=fac1,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 10)
    )

    assert res['total_solar_generation_kwh'] == Decimal('1000.0000')
    assert res['grid_consumption_kwh'] == Decimal('10000.0000')
    # Total = 10,000 + 1,000 = 11,000 kWh
    assert res['total_facility_consumption_kwh'] == Decimal('11000.0000')
    # Solar fraction = (1000 / 11000) * 100 = 9.09%
    assert res['solar_fraction_percentage'] == Decimal('9.09')
    assert res['self_consumption_percentage'] == Decimal('9.09')
    # Displaced cost = 1000 * 8.25 = ₹8,250
    assert res['estimated_cost_avoided_inr'] == Decimal('8250.00')

def test_cea_carbon_emissions_and_avoided_co2(renewables_setup):
    fac1 = renewables_setup['fac1']
    asset = renewables_setup['solar_asset']

    # Record 2,000 kWh of solar generation
    base_time = timezone.make_aware(datetime(2026, 3, 1, 12, 0))
    for i in range(10):
        t = base_time + timedelta(days=i)
        record_solar_generation_reading(
            asset=asset,
            timestamp=t,
            generation_kwh=Decimal('200.0000'),
            solar_irradiance_wm2=Decimal('700.00')
        )

    emissions = calculate_carbon_emissions(
        facility=fac1,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 10)
    )

    # Grid: 10,000 kWh * 0.8200 = 8,200 kg CO2
    # DG: 400 kWh * 0.6800 = 272 kg CO2
    # Total emissions = 8,472 kg CO2 = 8.472 tCO2e
    assert emissions['total_emissions_kg_co2'] == Decimal('8472.00')
    assert emissions['total_emissions_tco2e'] == Decimal('8.472')

    # Avoided emissions from solar: 2,000 kWh * 0.8200 = 1,640 kg CO2 = 1.640 tCO2e
    assert emissions['avoided_emissions_kg_co2'] == Decimal('1640.00')
    assert emissions['avoided_emissions_tco2e'] == Decimal('1.640')

def test_grid_event_logging(renewables_setup):
    fac1 = renewables_setup['fac1']
    start = timezone.now() - timedelta(minutes=45)
    end = timezone.now()

    event = record_grid_event(
        facility=fac1,
        event_type='grid_outage',
        start_time=start,
        end_time=end,
        fuel_consumed_litres=Decimal('35.50'),
        notes='Feeder trip due to storm.'
    )

    assert event.duration_minutes == Decimal('45.00')
    assert event.fuel_consumed_litres == Decimal('35.50')
    assert event.grid_restored is True

def test_renewables_api_endpoints_and_scoping(renewables_setup):
    admin = renewables_setup['admin']
    cust1 = renewables_setup['cust1']
    fac1 = renewables_setup['fac1']
    fac2 = renewables_setup['fac2']
    asset = renewables_setup['solar_asset']

    # Record sample reading
    record_solar_generation_reading(
        asset=asset,
        timestamp=timezone.now(),
        generation_kwh=Decimal('25.0000'),
        solar_irradiance_wm2=Decimal('650.00')
    )

    client = APIClient()

    # 1. Carbon Factors endpoint
    client.force_authenticate(user=admin)
    res_factors = client.get('/api/v1/renewables/carbon-factors/')
    assert res_factors.status_code == 200
    assert len(res_factors.data) == 4

    # 2. Solar Assets list
    res_assets = client.get('/api/v1/renewables/solar-assets/')
    assert res_assets.status_code == 200
    assert len(res_assets.data) == 1
    assert res_assets.data[0]['array_identifier'] == 'PV-ROOF-100KW'

    # 3. Generation readings
    res_gen = client.get('/api/v1/renewables/generation/')
    assert res_gen.status_code == 200
    assert len(res_gen.data) == 1

    # 4. Self-consumption endpoint (Customer 1 authorized for fac1)
    client.force_authenticate(user=cust1)
    res_sc = client.get(f'/api/v1/renewables/self-consumption/?facility_id={fac1.id}')
    assert res_sc.status_code == 200
    assert res_sc.data['facility_id'] == fac1.id

    # 5. Self-consumption scoping: Customer 1 requesting unassigned fac2 -> 404
    res_sc_unauth = client.get(f'/api/v1/renewables/self-consumption/?facility_id={fac2.id}')
    assert res_sc_unauth.status_code == 404

    # 6. Emissions endpoint
    res_em = client.get(f'/api/v1/renewables/emissions/?facility_id={fac1.id}')
    assert res_em.status_code == 200
    assert 'total_emissions_tco2e' in res_em.data

    # 7. Grid Event create & list
    res_evt_create = client.post('/api/v1/renewables/grid-events/', {
        'facility': fac1.id,
        'event_type': 'grid_outage',
        'start_time': timezone.now().isoformat(),
        'end_time': (timezone.now() + timedelta(minutes=30)).isoformat(),
        'fuel_consumed_litres': '20.00',
        'notes': 'Scheduled substation maintenance.'
    }, format='json')
    assert res_evt_create.status_code == 201

    res_evts = client.get(f'/api/v1/renewables/grid-events/?facility_id={fac1.id}')
    assert res_evts.status_code == 200
    assert len(res_evts.data) >= 1

