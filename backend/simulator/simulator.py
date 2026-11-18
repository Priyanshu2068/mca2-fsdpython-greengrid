"""
GreenGrid Environmental Simulator Engine.
Replays past environmental periods driven by NASA POWER hourly solar irradiance and temperature,
generating realistic 15-minute load telemetry for Indian commercial facilities.
"""

import math
import random
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from facilities.models import Facility, Meter
from ingestion.services import ingest_bulk_readings

NASA_POWER_API_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

class EnvironmentalSimulator:
    def __init__(self, facility: Facility):
        self.facility = facility
        self.latitude = float(facility.latitude or 12.9716) # Default Bengaluru
        self.longitude = float(facility.longitude or 77.5946)

    def fetch_nasa_power_data(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Retrieves hourly solar irradiance (ALLSKY_SFC_SW_DWN) and temperature (T2M) from NASA POWER.
        Falls back to realistic astronomical & thermodynamic model if external API is unreachable.
        """
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        params = {
            'parameters': 'T2M,ALLSKY_SFC_SW_DWN',
            'community': 'RE',
            'longitude': self.longitude,
            'latitude': self.latitude,
            'start': start_str,
            'end': end_str,
            'format': 'JSON'
        }
        try:
            resp = requests.get(NASA_POWER_API_URL, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('properties', {}).get('parameter', {})
        except Exception:
            pass # Fall back to synthetic astronomical model

        # Fallback synthetic generation
        hourly_temp = {}
        hourly_solar = {}
        curr = start_date
        while curr <= end_date:
            key = curr.strftime('%Y%m%d%H')
            hour = curr.hour
            # Diurnal temperature cycle: min at 05:00 AM, max at 14:00 PM (22°C to 34°C in India)
            temp = 24.0 + 8.0 * math.sin((hour - 8) * math.pi / 12)
            # Solar irradiance (W/m2): zero before 06:00 and after 18:00, peak at noon ~ 950 W/m2
            if 6 <= hour <= 18:
                solar = 950.0 * math.sin((hour - 6) * math.pi / 12)
            else:
                solar = 0.0

            hourly_temp[key] = round(temp, 2)
            hourly_solar[key] = max(0.0, round(solar, 2))
            curr += timedelta(hours=1)

        return {'T2M': hourly_temp, 'ALLSKY_SFC_SW_DWN': hourly_solar}

    def generate_15min_readings(self, start_date: datetime, days: int = 1) -> list:
        """
        Generates 15-minute readings across all meters registered for the facility.
        """
        end_date = start_date + timedelta(days=days)
        weather = self.fetch_nasa_power_data(start_date, end_date)
        temp_data = weather.get('T2M', {})
        solar_data = weather.get('ALLSKY_SFC_SW_DWN', {})

        meters = list(self.facility.meters.filter(is_active=True))
        if not meters:
            return []

        hvac_meter = next((m for m in meters if m.load_category == 'hvac'), None)
        lighting_meter = next((m for m in meters if m.load_category == 'lighting'), None)
        it_meter = next((m for m in meters if m.load_category == 'it_infrastructure'), None)
        solar_meter = next((m for m in meters if m.energy_source == 'solar'), None)
        incomer_meter = next((m for m in meters if m.load_category == 'main_incomer' and m.energy_source == 'grid'), None)

        readings = []
        curr_time = start_date

        while curr_time < end_date:
            hour_key = curr_time.strftime('%Y%m%d%H')
            ambient_temp = temp_data.get(hour_key, 28.0)
            solar_irr = solar_data.get(hour_key, 0.0)

            # 1. HVAC Load (Dependent on ambient temperature and office hours)
            # Base cooling 150 kW + 25 kW per degree above 24°C
            hvac_base = 120.0
            cooling_delta = max(0.0, ambient_temp - 24.0) * 22.0
            is_work_hours = 8 <= curr_time.hour <= 19 and curr_time.weekday() < 5
            hvac_kw = (hvac_base + cooling_delta) * (1.0 if is_work_hours else 0.35)
            hvac_kw += random.uniform(-5.0, 5.0)

            # 2. Lighting Load (Occupancy driven)
            lighting_kw = 55.0 * (1.0 if is_work_hours else 0.15) + random.uniform(-2.0, 2.0)

            # 3. IT Load (Flat 24x7 server load with slight daytime activity)
            it_kw = 95.0 + (10.0 if is_work_hours else 0.0) + random.uniform(-1.5, 1.5)

            # 4. Solar PV Generation (Directly correlated with solar irradiance)
            # 250 kWp rated array with PR ~ 0.80
            solar_kw = (250.0 * (solar_irr / 1000.0) * 0.80) if solar_irr > 0 else 0.0
            solar_kw = max(0.0, solar_kw)

            # 5. Main Incomer (Total net demand from grid)
            incomer_kw = max(20.0, (hvac_kw + lighting_kw + it_kw) - solar_kw)

            # Convert power (kW) to 15-minute energy (kWh): energy = kW * 0.25 h
            ts_iso = curr_time.isoformat()

            if hvac_meter:
                hvac_kwh = round(Decimal(str(hvac_kw * 0.25)), 4)
                readings.append({
                    'meter_identifier': hvac_meter.meter_identifier,
                    'timestamp': ts_iso,
                    'energy_kwh': max(Decimal('0.0000'), hvac_kwh),
                    'active_power_kw': round(Decimal(str(hvac_kw)), 4),
                    'power_factor': Decimal('0.950'),
                    'voltage_v': Decimal('415.00')
                })

            if lighting_meter:
                light_kwh = round(Decimal(str(lighting_kw * 0.25)), 4)
                readings.append({
                    'meter_identifier': lighting_meter.meter_identifier,
                    'timestamp': ts_iso,
                    'energy_kwh': max(Decimal('0.0000'), light_kwh),
                    'active_power_kw': round(Decimal(str(lighting_kw)), 4),
                    'power_factor': Decimal('0.980'),
                    'voltage_v': Decimal('415.00')
                })

            if it_meter:
                it_kwh = round(Decimal(str(it_kw * 0.25)), 4)
                readings.append({
                    'meter_identifier': it_meter.meter_identifier,
                    'timestamp': ts_iso,
                    'energy_kwh': max(Decimal('0.0000'), it_kwh),
                    'active_power_kw': round(Decimal(str(it_kw)), 4),
                    'power_factor': Decimal('0.985'),
                    'voltage_v': Decimal('415.00')
                })

            if solar_meter and solar_kw > 0:
                sol_kwh = round(Decimal(str(solar_kw * 0.25)), 4)
                readings.append({
                    'meter_identifier': solar_meter.meter_identifier,
                    'timestamp': ts_iso,
                    'energy_kwh': max(Decimal('0.0000'), sol_kwh),
                    'active_power_kw': round(Decimal(str(solar_kw)), 4),
                    'power_factor': Decimal('1.000'),
                    'voltage_v': Decimal('415.00')
                })

            if incomer_meter:
                inc_kwh = round(Decimal(str(incomer_kw * 0.25)), 4)
                readings.append({
                    'meter_identifier': incomer_meter.meter_identifier,
                    'timestamp': ts_iso,
                    'energy_kwh': max(Decimal('0.0000'), inc_kwh),
                    'active_power_kw': round(Decimal(str(incomer_kw)), 4),
                    'power_factor': Decimal('0.950'),
                    'voltage_v': Decimal('414.80')
                })

            curr_time += timedelta(minutes=15)

        return readings

    def run(self, start_date: datetime, days: int = 1) -> dict:
        readings = self.generate_15min_readings(start_date=start_date, days=days)
        if not readings:
            return {'status': 'skipped', 'message': 'No active meters found for facility.'}
        return ingest_bulk_readings(readings, source_type='simulator')

