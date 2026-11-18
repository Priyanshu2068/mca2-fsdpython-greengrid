import pytest
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from facilities.models import Facility, Meter
from simulator.simulator import EnvironmentalSimulator
from ingestion.models import RawReading

@pytest.fixture
def sim_facility(db):
    fac = Facility.objects.create(
        name='Alpha Tech Park',
        code='FAC-BLR-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('45000.00'),
        address='Bellandur',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560103'
    )
    Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-BLR-01-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-BLR-01-HVAC',
        name='Chiller Plant',
        energy_source='grid',
        load_category='hvac'
    )
    Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-BLR-01-SOL',
        name='Rooftop Solar PV',
        energy_source='solar',
        load_category='main_incomer'
    )
    return fac

@pytest.mark.django_db
def test_simulator_generates_readings(sim_facility):
    sim = EnvironmentalSimulator(sim_facility)
    start = timezone.make_aware(datetime(2026, 3, 1, 0, 0))
    readings = sim.generate_15min_readings(start_date=start, days=1)

    assert len(readings) > 0
    # 24 hours * 4 intervals per hour = 96 intervals per meter
    # We registered 3 meters: incomer, hvac, solar
    assert len(readings) >= 96 * 2

    # Check non-negative constraint
    for r in readings:
        assert r['energy_kwh'] >= 0

@pytest.mark.django_db
def test_simulator_run_persists_to_ingestion(sim_facility):
    sim = EnvironmentalSimulator(sim_facility)
    start = timezone.make_aware(datetime(2026, 3, 1, 0, 0))
    result = sim.run(start_date=start, days=1)

    assert result['status'] == 'processed'
    assert result['accepted'] > 0
    assert RawReading.objects.filter(meter__facility=sim_facility).count() > 0

