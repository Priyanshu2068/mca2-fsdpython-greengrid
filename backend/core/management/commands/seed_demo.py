"""
Seed a demo dataset (users, facilities, meters, tariffs, bills, solar, grid events, benchmarks)
so the web frontend has something to show. Idempotent: safe to re-run.

Usage: python manage.py seed_demo [--days 30]
"""
import math
import random
from datetime import timedelta, date
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from accounts.models import CustomUser
from analytics.models import DailyRollup, AnomalyAlert
from ingestion.models import RawReading
from facilities.models import Facility, Building, Meter, UserFacilityAssignment
from billing.models import UtilityProvider, TariffStructure, UtilityBill
from billing.services import record_utility_bill
from benchmarking.models import BuildingBenchmark
from renewables.models import SolarAsset, SolarGenerationReading, GridEvent, CarbonEmissionFactor
from recommendations.services import ensure_standard_rules_exist

DEMO_PASSWORD = 'GreenGrid@123'

FACILITIES = [
    dict(code='BLR-TP-01', name='Bengaluru Tech Park', facility_type='tech_park', area='42000', city='Bengaluru',
         state='Karnataka', pin='560100', lat='12.9716', lon='77.5946', kva='900'),
    dict(code='MUM-OF-01', name='Mumbai Corporate Tower', facility_type='commercial_office', area='28000',
         city='Mumbai', state='Maharashtra', pin='400051', lat='19.0760', lon='72.8777', kva='650'),
]
METERS = [
    ('INC', 'Main Incomer', 'grid', 'main_incomer'),
    ('HVAC', 'Chiller Plant', 'grid', 'hvac'),
    ('LGT', 'Lighting Circuits', 'grid', 'lighting'),
    ('IT', 'Server Room', 'grid', 'it_infrastructure'),
    ('SOL', 'Rooftop Solar Inverter', 'solar', 'main_incomer'),
    ('DG', 'Diesel Generator', 'diesel_generator', 'main_incomer'),
]


class Command(BaseCommand):
    help = 'Seeds demo data for the GreenGrid web frontend.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **opts):
        days = opts['days']
        random.seed(42)
        now = timezone.now()

        admin, _ = CustomUser.objects.get_or_create(
            email='admin@greengrid.test',
            defaults=dict(first_name='Asha', last_name='Admin', role='admin', is_staff=True, is_superuser=True))
        admin.set_password(DEMO_PASSWORD)
        admin.save()
        cust, _ = CustomUser.objects.get_or_create(
            email='customer@greengrid.test',
            defaults=dict(first_name='Rohan', last_name='Customer', role='customer'))
        cust.set_password(DEMO_PASSWORD)
        cust.save()
        eng, _ = CustomUser.objects.get_or_create(
            email='engineer@greengrid.test',
            defaults=dict(first_name='Karthik', last_name='Nair', role='field_engineer'))
        eng.set_password(DEMO_PASSWORD)
        eng.save()

        # Reference data
        for t, med, top, bot in [('commercial_office', 160, 110, 220), ('tech_park', 200, 140, 280),
                                 ('hospital', 250, 180, 340), ('retail_mall', 300, 210, 400),
                                 ('hotel', 220, 150, 300), ('educational_campus', 90, 60, 130)]:
            BuildingBenchmark.objects.get_or_create(facility_type=t, defaults=dict(
                median_eui_kwh_sqm_year=med, top_20_percentile_eui=top, bottom_20_percentile_eui=bot))
        for src, f, ref in [('grid', '0.7100', 'CEA CO2 Baseline Database v19'),
                            ('diesel_generator', '0.8100', 'IPCC 2006 diesel genset'),
                            ('solar', '0.0000', 'Zero operational emissions'),
                            ('natural_gas', '0.2020', 'IPCC natural gas')]:
            CarbonEmissionFactor.objects.get_or_create(energy_source=src, defaults=dict(
                co2_kg_per_kwh=f, source_reference=ref))
        ensure_standard_rules_exist()

        prov, _ = UtilityProvider.objects.get_or_create(code='BESCOM', defaults=dict(
            name='Bangalore Electricity Supply Company', state='Karnataka',
            website='https://bescom.karnataka.gov.in', customer_care_phone='1912'))
        tariff, _ = TariffStructure.objects.get_or_create(tariff_code='BESCOM-HT2A', defaults=dict(
            provider=prov, tariff_name='HT-2(a) Commercial', effective_from=date(2025, 4, 1),
            base_energy_rate_inr='8.5000', peak_hour_rate_inr='10.2000', off_peak_rate_inr='7.2000',
            demand_charge_inr_per_kva='350.00', fixed_charge_monthly_inr='25000.00'))

        for spec in FACILITIES:
            fac, created = Facility.objects.get_or_create(code=spec['code'], defaults=dict(
                name=spec['name'], facility_type=spec['facility_type'], gross_floor_area_sqm=spec['area'],
                operating_hours_per_week='60', address=f"Business District, {spec['city']}", city=spec['city'],
                state=spec['state'], pin_code=spec['pin'], latitude=spec['lat'], longitude=spec['lon'],
                sanctioned_demand_kva=spec['kva']))
            for u in (admin, cust, eng):
                UserFacilityAssignment.objects.get_or_create(user=u, facility=fac)
            b, _ = Building.objects.get_or_create(facility=fac, code='B1', defaults=dict(
                name='Block A', total_floors=12, floor_area_sqm=spec['area']))
            for code, name, src, cat in METERS:
                Meter.objects.get_or_create(meter_identifier=f"{spec['code']}-{code}", defaults=dict(
                    facility=fac, building=b, name=name, energy_source=src, load_category=cat))
            self.stdout.write(f"Facility {fac.name} (id={fac.id})")

            if not RawReading.objects.filter(meter__facility=fac).exists():
                # chunked: ingestion caps batches at INGESTION_MAX_BATCH_SIZE readings
                for d in range(days, -1, -5):
                    chunk = min(5, d + 1)
                    start = (now - timedelta(days=d)).strftime('%Y-%m-%d')
                    call_command('run_simulator', facility_id=fac.id, days=chunk, start_date=start)

            self._seed_dg_and_solar(fac, now, days)

        call_command('rollup_hourly', hours_back=(days + 2) * 24)
        call_command('rollup_daily', days_back=days + 2)
        call_command('detect_anomalies')

        # Bills for the Bengaluru facility (last two cycles) -> reconciliation
        fac = Facility.objects.get(code='BLR-TP-01')
        today = timezone.localdate()
        for i, (kwh_factor, status) in enumerate([(1.004, 'paid'), (1.045, 'unpaid')]):
            end = today - timedelta(days=15 * i)
            begin = end - timedelta(days=14)
            metered = DailyRollup.objects.filter(
                meter__facility=fac, meter__load_category='main_incomer', meter__energy_source='grid',
                rollup_date__gte=begin, rollup_date__lte=end).aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('1000')
            billed = (metered * Decimal(str(kwh_factor))).quantize(Decimal('0.0001'))
            num = f'BESCOM-{end:%Y%m%d}'
            if not UtilityBill.objects.filter(bill_number=num).exists():
                record_utility_bill(fac, tariff, num, begin, end, end + timedelta(days=15), billed,
                                    Decimal('610.00'), (billed * Decimal('8.9')).quantize(Decimal('0.01')),
                                    payment_status=status)

        self._alerts(fac, now)
        call_command('compute_benchmarks')
        call_command('generate_recommendations')
        self.stdout.write(self.style.SUCCESS(
            f"Done. Demo accounts: admin@greengrid.test, customer@greengrid.test, engineer@greengrid.test / {DEMO_PASSWORD}"))

    def _seed_dg_and_solar(self, fac, now, days):
        self._solar(fac, now, days)
        self._events(fac, now)

        dg_meter = fac.meters.filter(energy_source='diesel_generator').first()
        sol_meter = fac.meters.filter(energy_source='solar').first()
        inc_meter = fac.meters.filter(load_category='main_incomer', energy_source='grid').first()

        # DG readings during logged outages where fuel was used
        if dg_meter and not RawReading.objects.filter(meter=dg_meter).exists():
            dg_rows = []
            for ev in GridEvent.objects.filter(facility=fac, fuel_consumed_litres__gt=0):
                total_kwh = float(ev.fuel_consumed_litres) * 3.8
                mins = int(ev.duration_minutes)
                intervals = max(1, math.ceil(mins / 15))
                kwh_per_int = total_kwh / intervals
                kw_per_int = kwh_per_int * 4.0
                curr_t = ev.start_time
                for _ in range(intervals):
                    dg_rows.append(RawReading(
                        meter=dg_meter,
                        timestamp=curr_t,
                        energy_kwh=Decimal(str(round(kwh_per_int, 4))),
                        active_power_kw=Decimal(str(round(kw_per_int, 4))),
                        power_factor=Decimal('0.880'),
                        voltage_v=Decimal('415.00')
                    ))
                    if inc_meter:
                        RawReading.objects.filter(meter=inc_meter, timestamp=curr_t).update(
                            voltage_v=Decimal('0.00'), active_power_kw=Decimal('0.0000'), energy_kwh=Decimal('0.0000')
                        )
                    curr_t += timedelta(minutes=15)
            if dg_rows:
                RawReading.objects.bulk_create(dg_rows, ignore_conflicts=True)

        # Solar meter readings matching SolarGenerationReading
        if sol_meter and not RawReading.objects.filter(meter=sol_meter).exists():
            sol_readings = SolarGenerationReading.objects.filter(asset__facility=fac)
            sol_rows = []
            for sr in sol_readings:
                kwh_15 = float(sr.generation_kwh) / 4.0
                kw = float(sr.generation_kwh)
                for step in range(4):
                    sol_rows.append(RawReading(
                        meter=sol_meter,
                        timestamp=sr.timestamp + timedelta(minutes=15 * step),
                        energy_kwh=Decimal(str(round(kwh_15, 4))),
                        active_power_kw=Decimal(str(round(kw, 4))),
                        power_factor=Decimal('1.000'),
                        voltage_v=Decimal('415.00')
                    ))
            if sol_rows:
                RawReading.objects.bulk_create(sol_rows, ignore_conflicts=True)

    def _solar(self, fac, now, days):
        asset, _ = SolarAsset.objects.get_or_create(array_identifier=f'{fac.code}-PV1', defaults=dict(
            facility=fac, name='Rooftop PV Array 1', rated_capacity_kwp='250', commissioned_date=date(2024, 6, 1)))
        rows = []
        t0 = (now - timedelta(days=days)).replace(minute=0, second=0, microsecond=0)
        for h in range(days * 24):
            ts = t0 + timedelta(hours=h)
            local_h = timezone.localtime(ts).hour
            irr = max(0.0, 950 * math.sin((local_h - 6) * math.pi / 12)) if 6 <= local_h <= 18 else 0.0
            irr *= random.uniform(0.7, 1.0)
            kwh = 250 * (irr / 1000) * 0.8
            rows.append(SolarGenerationReading(
                asset=asset, timestamp=ts, generation_kwh=round(kwh, 4), solar_irradiance_wm2=round(irr, 2),
                ambient_temp_celsius=round(24 + 8 * math.sin((local_h - 8) * math.pi / 12), 2),
                performance_ratio='0.80'))
        SolarGenerationReading.objects.bulk_create(rows, ignore_conflicts=True)

    def _events(self, fac, now):
        for days_ago, kind, mins, fuel in [(21, 'grid_outage', 95, 140), (9, 'voltage_sag', 1, 0),
                                           (4, 'grid_outage', 40, 62), (2, 'frequency_aberration', 3, 0)]:
            st = now - timedelta(days=days_ago, hours=3)
            GridEvent.objects.create(facility=fac, event_type=kind, start_time=st,
                                     end_time=st + timedelta(minutes=mins), duration_minutes=mins,
                                     fuel_consumed_litres=fuel, grid_restored=True,
                                     notes='Auto-logged by demo seed')

    def _alerts(self, fac, now):
        if AnomalyAlert.objects.filter(facility=fac).exists():
            return
        m = {x.meter_identifier.split('-')[-1]: x for x in fac.meters.all()}
        for key, kind, sev, reason, base, obs, dev, hrs in [
            ('HVAC', 'consumption_spike', 'high', 'Chiller plant drew 1.6x its 4-week median for this hour.', 118, 189, 1.60, 5),
            ('INC', 'low_power_factor', 'medium', 'Average power factor fell to 0.86 (threshold 0.90).', 0.95, 0.86, 0.91, 30),
            ('IT', 'meter_silent', 'low', 'No readings received for more than 2 hours.', 4, 0, 0, 52),
        ]:
            AnomalyAlert.objects.create(
                facility=fac, meter=m[key], anomaly_type=kind, severity=sev, reason=reason,
                baseline_value=base, observed_value=obs, deviation_factor=dev, status='open',
                detected_at=now - timedelta(hours=hrs))
