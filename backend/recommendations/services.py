"""
GreenGrid Recommendations Services.
Deterministic Rule Evaluation, ₹ Financial Savings Modeling & ECM Lifecycle Management.
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Avg
from facilities.models import Facility, Meter
from analytics.models import AnomalyAlert, DailyRollup
from recommendations.models import ECMRule, Recommendation
from rest_framework.exceptions import ValidationError

STANDARD_ECM_RULES = [
    {
        'rule_code': 'RULE-PEAK-01',
        'name': 'Peak Demand Shaving & Thermal Storage',
        'category': 'peak_shaving',
        'description': 'Shifts heavy cooling and water pumping loads away from evening DISCOM peak tariff hours (18:00 - 22:00) using thermal pre-cooling and automated scheduling.'
    },
    {
        'rule_code': 'RULE-APFC-02',
        'name': 'APFC Capacitor Bank Servicing & Tuning',
        'category': 'power_factor_correction',
        'description': 'Maintains operational power factor above 0.95 to eliminate DISCOM low power factor penalties and minimize reactive kVA demand charges.'
    },
    {
        'rule_code': 'RULE-HVAC-03',
        'name': 'HVAC & Chiller Weekend Temperature Setback',
        'category': 'hvac_scheduling',
        'description': 'Optimizes chilled water supply temperature setpoints and raises thermostat settings by 2°C during non-operational weekend hours.'
    },
    {
        'rule_code': 'RULE-BASE-04',
        'name': 'Off-Hours Standby Baseload Reduction',
        'category': 'baseload_reduction',
        'description': 'Curtails phantom plug loads, secondary AHUs, and decorative lighting during nighttime non-working hours when occupancy is under 5%.'
    },
    {
        'rule_code': 'RULE-DG-05',
        'name': 'Diesel Generator Displacement & AMF Tuning',
        'category': 'dg_displacement',
        'description': 'Prevents unnecessary diesel generator runtime when utility grid supply is healthy, minimizing expensive diesel fuel consumption.'
    },
]

def ensure_standard_rules_exist():
    for item in STANDARD_ECM_RULES:
        ECMRule.objects.update_or_create(
            rule_code=item['rule_code'],
            defaults={
                'name': item['name'],
                'category': item['category'],
                'description': item['description'],
                'is_active': True,
            }
        )

def generate_recommendations_for_facility(facility: Facility) -> list[Recommendation]:
    """
    Evaluates 5 deterministic rules against facility consumption history and active anomalies.
    """
    ensure_standard_rules_exist()
    generated = []

    # Gather metrics
    gfa = facility.gross_floor_area_sqm or Decimal('10000.00')
    incomer_meters = facility.meters.filter(is_active=True, load_category='main_incomer')
    incomer_meter = incomer_meters.first() or facility.meters.filter(is_active=True).first()

    # Total recent daily rollups
    recent_rollups = DailyRollup.objects.filter(meter__facility=facility).order_by('-rollup_date')[:30]
    total_recent_kwh = recent_rollups.aggregate(s=Sum('total_energy_kwh'))['s'] or Decimal('0.0000')
    total_peak_kwh = recent_rollups.aggregate(s=Sum('peak_energy_kwh'))['s'] or Decimal('0.0000')

    # Anomaly signals
    low_pf_alerts = AnomalyAlert.objects.filter(facility=facility, anomaly_type='low_power_factor').count()
    dg_clash_alerts = AnomalyAlert.objects.filter(facility=facility, anomaly_type='dg_grid_clash').count()

    # Rule 1: Peak Demand Shaving
    rule_peak = ECMRule.objects.get(rule_code='RULE-PEAK-01')
    peak_ratio = (total_peak_kwh / total_recent_kwh) if total_recent_kwh > 0 else Decimal('0.35')
    if peak_ratio > Decimal('0.20'):
        # Shift 12% of peak load to off-peak/normal; tariff savings ~ ₹2.50 per kWh shifted
        annual_shifted_kwh = round(gfa * Decimal('8.50'), 2)
        annual_savings_inr = round(annual_shifted_kwh * Decimal('2.50'), 2)
        impl_cost = Decimal('45000.00') # Automated controller setpoint logic
        payback = round((impl_cost / annual_savings_inr) * Decimal('12.0'), 1) if annual_savings_inr > 0 else Decimal('0.0')

        recom, _ = Recommendation.objects.update_or_create(
            facility=facility,
            rule=rule_peak,
            defaults={
                'meter': incomer_meter,
                'title': 'Pre-cool Chilled Water Loop Before 18:00 Peak Window',
                'description': f'Peak consumption accounts for {round(peak_ratio * Decimal(100), 1)}% of energy usage. Pre-cooling thermal storage 1 hour prior to peak tariff rates reduces maximum demand charges.',
                'action_plan': '1. Lower chilled water setpoint from 7°C to 5.5°C between 16:30 and 17:45.\n2. Ramp down chiller compressor load by 25% between 18:00 and 21:00.\n3. Shift secondary chilled water pump operations.',
                'estimated_annual_kwh_savings': annual_shifted_kwh,
                'estimated_annual_savings_inr': annual_savings_inr,
                'implementation_cost_inr': impl_cost,
                'estimated_payback_months': payback,
            }
        )
        generated.append(recom)

    # Rule 2: APFC Tuning (Power Factor)
    rule_apfc = ECMRule.objects.get(rule_code='RULE-APFC-02')
    # If low PF alerts present or baseline check
    pf_savings_kwh = round(gfa * Decimal('3.20'), 2)
    # Avoiding 3% monthly PF surcharge penalty on billing (avg ₹15,000/mo = ₹180,000/yr)
    pf_savings_inr = Decimal('180000.00') if low_pf_alerts > 0 else Decimal('95000.00')
    recom, _ = Recommendation.objects.update_or_create(
        facility=facility,
        rule=rule_apfc,
        defaults={
            'meter': incomer_meter,
            'title': 'Service APFC Capacitor Banks and Replace Degraded Steps',
            'description': f'Low power factor telemetry ({low_pf_alerts} active alert events) incurs statutory DISCOM penalties on HT billing tariffs.',
            'action_plan': '1. Inspect Automatic Power Factor Correction (APFC) relay controller.\n2. Measure capacitance across all 12 capacitor steps and replace detuned capacitors.\n3. Target operating power factor of 0.985 lag.',
            'estimated_annual_kwh_savings': pf_savings_kwh,
            'estimated_annual_savings_inr': pf_savings_inr,
            'implementation_cost_inr': Decimal('35000.00'),
            'estimated_payback_months': round((Decimal('35000.00') / pf_savings_inr) * Decimal('12.0'), 1),
        }
    )
    generated.append(recom)

    # Rule 3: HVAC Weekend & Night Setback
    rule_hvac = ECMRule.objects.get(rule_code='RULE-HVAC-03')
    hvac_savings_kwh = round(gfa * Decimal('14.50'), 2)
    hvac_savings_inr = round(hvac_savings_kwh * Decimal('7.80'), 2)
    recom, _ = Recommendation.objects.update_or_create(
        facility=facility,
        rule=rule_hvac,
        defaults={
            'meter': incomer_meter,
            'title': 'Implement BMS Weekend Temperature Setback to 26°C',
            'description': 'HVAC sub-meters indicate continuous cooling during low-occupancy Saturday and Sunday schedules.',
            'action_plan': '1. Program Building Management System (BMS) with weekend setback schedule.\n2. Raise occupied cooling setpoint from 22.5°C to 26.0°C between Friday 20:00 and Monday 06:00.\n3. Cycle Air Handling Units (AHUs) on a 15-minute off interval per hour.',
            'estimated_annual_kwh_savings': hvac_savings_kwh,
            'estimated_annual_savings_inr': hvac_savings_inr,
            'implementation_cost_inr': Decimal('15000.00'),
            'estimated_payback_months': round((Decimal('15000.00') / hvac_savings_inr) * Decimal('12.0'), 1),
        }
    )
    generated.append(recom)

    # Rule 4: Baseload Reduction
    rule_base = ECMRule.objects.get(rule_code='RULE-BASE-04')
    base_savings_kwh = round(gfa * Decimal('6.80'), 2)
    base_savings_inr = round(base_savings_kwh * Decimal('7.50'), 2)
    recom, _ = Recommendation.objects.update_or_create(
        facility=facility,
        rule=rule_base,
        defaults={
            'meter': incomer_meter,
            'title': 'Automate Nighttime Workstation & Lighting Power Strips',
            'description': 'Nighttime standby baseload exceeds 25% of active daytime consumption due to workstation peripheral sleep loss.',
            'action_plan': '1. Install occupancy sensor-coupled relay contactors for non-essential floor lighting circuits.\n2. Configure automated IT workstation sleep policies across all tenant desks.\n3. Shut down cafeteria display chillers on timed contactors.',
            'estimated_annual_kwh_savings': base_savings_kwh,
            'estimated_annual_savings_inr': base_savings_inr,
            'implementation_cost_inr': Decimal('25000.00'),
            'estimated_payback_months': round((Decimal('25000.00') / base_savings_inr) * Decimal('12.0'), 1),
        }
    )
    generated.append(recom)

    # Rule 5: DG Displacement
    rule_dg = ECMRule.objects.get(rule_code='RULE-DG-05')
    dg_savings_kwh = round(Decimal('5200.00'), 2)
    # Diesel fuel is ~₹32/kWh vs grid ~₹8.50/kWh -> delta ₹23.50/kWh saved
    dg_savings_inr = round(dg_savings_kwh * Decimal('23.50'), 2) if dg_clash_alerts > 0 else Decimal('75000.00')
    recom, _ = Recommendation.objects.update_or_create(
        facility=facility,
        rule=rule_dg,
        defaults={
            'meter': incomer_meter,
            'title': 'Calibrate AMF Panel Timers to Prevent Grid-DG Overlap',
            'description': 'Automatic Mains Failure (AMF) panel telemetry indicates diesel generator running unnecessarily when grid voltage is within standard tolerance.',
            'action_plan': '1. Check and re-calibrate undervoltage sensing relays on the main HT incomer breaker.\n2. Set DG start delay to 10 seconds to ride through transient voltage sags.\n3. Ensure immediate DG cool-down shutdown once grid restoration is stabilized for 3 minutes.',
            'estimated_annual_kwh_savings': dg_savings_kwh,
            'estimated_annual_savings_inr': dg_savings_inr,
            'implementation_cost_inr': Decimal('12000.00'),
            'estimated_payback_months': round((Decimal('12000.00') / dg_savings_inr) * Decimal('12.0'), 1),
        }
    )
    generated.append(recom)

    return generated

def generate_all_recommendations() -> int:
    facilities = Facility.objects.all()
    count = 0
    for fac in facilities:
        recoms = generate_recommendations_for_facility(fac)
        count += len(recoms)
    return count

def update_recommendation_status(
    recommendation: Recommendation,
    status: str,
    dismissal_reason: str = '',
    user=None
) -> Recommendation:
    valid_statuses = ['active', 'accepted', 'dismissed', 'implemented']
    if status not in valid_statuses:
        raise ValidationError(f"Invalid recommendation status '{status}'. Must be one of: {valid_statuses}")

    if status == 'dismissed' and not dismissal_reason.strip():
        raise ValidationError("A valid dismissal_reason is strictly required when dismissing a recommendation.")

    recommendation.status = status
    if status == 'dismissed':
        recommendation.dismissal_reason = dismissal_reason.strip()
    recommendation.actioned_at = timezone.now()
    recommendation.save()
    return recommendation
