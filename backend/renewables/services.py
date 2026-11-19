"""
GreenGrid Renewables Services.
Solar Generation Accounting, Performance Ratio (PR), Self-Consumption & CEA Scope 2 Carbon Emissions.
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from facilities.models import Facility, Meter
from analytics.models import DailyRollup
from renewables.models import (
    SolarAsset,
    SolarGenerationReading,
    GridEvent,
    CarbonEmissionFactor,
)

DEFAULT_CEA_EMISSION_FACTORS = [
    {
        'energy_source': 'grid',
        'co2_kg_per_kwh': Decimal('0.8200'),
        'source_reference': 'Central Electricity Authority (CEA) India Baseline CO2 Database Version 19 (Grid Average)'
    },
    {
        'energy_source': 'diesel_generator',
        'co2_kg_per_kwh': Decimal('0.6800'),
        'source_reference': 'CEA India / CPCB Emission Norms for Captive Stationary Diesel Generator Sets'
    },
    {
        'energy_source': 'natural_gas',
        'co2_kg_per_kwh': Decimal('0.4900'),
        'source_reference': 'IPCC / CEA India Baseline for Piped Natural Gas Co-generation'
    },
    {
        'energy_source': 'solar',
        'co2_kg_per_kwh': Decimal('0.0000'),
        'source_reference': 'GHG Protocol Scope 2 Guidance (Zero Direct Emissions for On-Site Solar PV)'
    },
]

def ensure_default_emission_factors():
    for item in DEFAULT_CEA_EMISSION_FACTORS:
        CarbonEmissionFactor.objects.update_or_create(
            energy_source=item['energy_source'],
            defaults={
                'co2_kg_per_kwh': item['co2_kg_per_kwh'],
                'source_reference': item['source_reference']
            }
        )

def record_solar_generation_reading(
    asset: SolarAsset,
    timestamp,
    generation_kwh: Decimal,
    solar_irradiance_wm2: Decimal = Decimal('0.00'),
    ambient_temp_celsius: Decimal = Decimal('25.00'),
    performance_ratio: Decimal = None
) -> SolarGenerationReading:
    """
    Persists a 15-minute solar generation reading with computed or provided Performance Ratio (PR).
    """
    if performance_ratio is None:
        if solar_irradiance_wm2 > 0:
            # Expected generation in 15 mins (0.25h) = Capacity (kWp) * (G / 1000) * 0.25
            expected_kwh = asset.rated_capacity_kwp * (solar_irradiance_wm2 / Decimal('1000.00')) * Decimal('0.25')
            if expected_kwh > 0:
                raw_pr = generation_kwh / expected_kwh
                performance_ratio = min(Decimal('1.00'), max(Decimal('0.00'), round(raw_pr, 2)))
            else:
                performance_ratio = Decimal('0.80')
        else:
            performance_ratio = Decimal('0.00') if generation_kwh == 0 else Decimal('0.80')

    reading, _ = SolarGenerationReading.objects.update_or_create(
        asset=asset,
        timestamp=timestamp,
        defaults={
            'generation_kwh': generation_kwh,
            'solar_irradiance_wm2': solar_irradiance_wm2,
            'ambient_temp_celsius': ambient_temp_celsius,
            'performance_ratio': performance_ratio,
        }
    )
    return reading

def calculate_solar_self_consumption(facility: Facility, start_date=None, end_date=None) -> dict:
    """
    Calculates facility solar generation, total consumption, self-consumption %, and avoided grid expenditure.
    """
    # 1. Solar generation sum
    gen_qs = SolarGenerationReading.objects.filter(asset__facility=facility)
    if start_date:
        gen_qs = gen_qs.filter(timestamp__date__gte=start_date)
    if end_date:
        gen_qs = gen_qs.filter(timestamp__date__lte=end_date)
    total_solar_kwh = gen_qs.aggregate(s=Sum('generation_kwh'))['s'] or Decimal('0.0000')

    # 2. Total facility consumption from DailyRollups
    rollup_qs = DailyRollup.objects.filter(meter__facility=facility)
    if start_date:
        rollup_qs = rollup_qs.filter(rollup_date__gte=start_date)
    if end_date:
        rollup_qs = rollup_qs.filter(rollup_date__lte=end_date)

    # Main incomer / grid total
    grid_kwh = (
        rollup_qs.filter(meter__energy_source='grid', meter__load_category='main_incomer')
        .aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')
    )
    if grid_kwh == 0:
        grid_kwh = rollup_qs.aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')

    total_facility_kwh = grid_kwh + total_solar_kwh

    if total_facility_kwh > 0:
        # What % of solar was consumed on site (cap at 100%)
        self_consumption_pct = min(Decimal('100.00'), round((total_solar_kwh / total_facility_kwh) * Decimal('100.00'), 2))
        solar_fraction_pct = min(Decimal('100.00'), round((total_solar_kwh / total_facility_kwh) * Decimal('100.00'), 2))
    else:
        self_consumption_pct = Decimal('100.00')
        solar_fraction_pct = Decimal('0.00')

    # Average commercial grid displacement savings (₹8.25/kWh)
    displaced_grid_cost_inr = round(total_solar_kwh * Decimal('8.25'), 2)

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'total_solar_generation_kwh': total_solar_kwh,
        'grid_consumption_kwh': grid_kwh,
        'total_facility_consumption_kwh': total_facility_kwh,
        'self_consumption_percentage': self_consumption_pct,
        'solar_fraction_percentage': solar_fraction_pct,
        'estimated_cost_avoided_inr': displaced_grid_cost_inr,
    }

def calculate_carbon_emissions(facility: Facility, start_date=None, end_date=None) -> dict:
    """
    Computes GHG Protocol Scope 2 emissions based on CEA India factors.
    """
    ensure_default_emission_factors()

    factors = {f.energy_source: f.co2_kg_per_kwh for f in CarbonEmissionFactor.objects.all()}
    grid_factor = factors.get('grid', Decimal('0.8200'))
    dg_factor = factors.get('diesel_generator', Decimal('0.6800'))
    gas_factor = factors.get('natural_gas', Decimal('0.4900'))

    rollup_qs = DailyRollup.objects.filter(meter__facility=facility)
    if start_date:
        rollup_qs = rollup_qs.filter(rollup_date__gte=start_date)
    if end_date:
        rollup_qs = rollup_qs.filter(rollup_date__lte=end_date)

    grid_kwh = rollup_qs.filter(meter__energy_source='grid').aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')
    dg_kwh = rollup_qs.filter(meter__energy_source='diesel_generator').aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')
    gas_kwh = rollup_qs.filter(meter__energy_source='gas').aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')

    # Solar generation
    solar_qs = SolarGenerationReading.objects.filter(asset__facility=facility)
    if start_date:
        solar_qs = solar_qs.filter(timestamp__date__gte=start_date)
    if end_date:
        solar_qs = solar_qs.filter(timestamp__date__lte=end_date)
    solar_kwh = solar_qs.aggregate(s=Sum('generation_kwh'))['s'] or Decimal('0.0000')

    grid_emissions = round(grid_kwh * grid_factor, 2)
    dg_emissions = round(dg_kwh * dg_factor, 2)
    gas_emissions = round(gas_kwh * gas_factor, 2)
    solar_emissions = Decimal('0.00')

    total_emissions_kg = grid_emissions + dg_emissions + gas_emissions
    total_tco2e = round(total_emissions_kg / Decimal('1000.00'), 3)
    avoided_emissions_kg = round(solar_kwh * grid_factor, 2)
    avoided_tco2e = round(avoided_emissions_kg / Decimal('1000.00'), 3)

    return {
        'facility_id': facility.id,
        'facility_name': facility.name,
        'breakdown_by_source': {
            'grid': {
                'energy_kwh': grid_kwh,
                'factor_kg_per_kwh': grid_factor,
                'emissions_kg_co2': grid_emissions,
            },
            'diesel_generator': {
                'energy_kwh': dg_kwh,
                'factor_kg_per_kwh': dg_factor,
                'emissions_kg_co2': dg_emissions,
            },
            'natural_gas': {
                'energy_kwh': gas_kwh,
                'factor_kg_per_kwh': gas_factor,
                'emissions_kg_co2': gas_emissions,
            },
            'solar': {
                'energy_kwh': solar_kwh,
                'factor_kg_per_kwh': Decimal('0.0000'),
                'emissions_kg_co2': solar_emissions,
            },
        },
        'total_emissions_kg_co2': total_emissions_kg,
        'total_emissions_tco2e': total_tco2e,
        'avoided_emissions_kg_co2': avoided_emissions_kg,
        'avoided_emissions_tco2e': avoided_tco2e,
    }

def record_grid_event(
    facility: Facility,
    event_type: str,
    start_time,
    end_time=None,
    fuel_consumed_litres: Decimal = Decimal('0.00'),
    notes: str = ''
) -> GridEvent:
    duration = None
    grid_restored = False
    if end_time:
        diff = (end_time - start_time).total_seconds()
        duration = round(Decimal(str(diff)) / Decimal('60.0'), 2)
        grid_restored = True

    event = GridEvent.objects.create(
        facility=facility,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration,
        fuel_consumed_litres=fuel_consumed_litres,
        grid_restored=grid_restored,
        notes=notes
    )
    return event

