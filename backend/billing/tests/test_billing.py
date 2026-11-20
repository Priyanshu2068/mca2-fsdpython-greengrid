import pytest
from datetime import date
from decimal import Decimal
from rest_framework.test import APIClient
from accounts.models import CustomUser
from facilities.models import Facility, Meter
from analytics.models import DailyRollup
from billing.models import UtilityProvider, TariffStructure, UtilityBill, BillReconciliation
from billing.services import record_utility_bill, reconcile_utility_bill

@pytest.fixture
def billing_setup(db):
    admin = CustomUser.objects.create_superuser(email='adm@gg.in', password='pass')
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
    incomer = Meter.objects.create(
        facility=fac,
        meter_identifier='MTR-INC',
        name='Main Incomer',
        energy_source='grid',
        load_category='main_incomer'
    )
    provider = UtilityProvider.objects.create(
        name='BESCOM',
        code='BESCOM',
        state='Karnataka'
    )
    tariff = TariffStructure.objects.create(
        provider=provider,
        tariff_code='BESCOM-HT2A',
        tariff_name='Commercial HT-2A',
        effective_from=date(2024, 4, 1),
        base_energy_rate_inr=Decimal('7.4500'),
        peak_hour_rate_inr=Decimal('9.5000'),
        off_peak_rate_inr=Decimal('6.2000'),
        demand_charge_inr_per_kva=Decimal('310.00')
    )

    # Populate daily rollups for March 2026: 10 days of 10,000 kWh = 100,000 metered kWh
    for day in range(1, 11):
        DailyRollup.objects.create(
            meter=incomer,
            rollup_date=date(2026, 3, day),
            total_energy_kwh=Decimal('10000.0000'),
            peak_demand_kw=Decimal('1500.0000')
        )

    return admin, fac, tariff

@pytest.mark.django_db
def test_effective_cost_per_kwh_calculation(billing_setup):
    admin, fac, tariff = billing_setup
    # Billed 100,000 kWh for ₹800,000 -> effective cost = ₹8.0000/kWh
    bill = record_utility_bill(
        facility=fac,
        tariff=tariff,
        bill_number='BILL-2026-03',
        billing_cycle_start=date(2026, 3, 1),
        billing_cycle_end=date(2026, 3, 10),
        due_date=date(2026, 3, 25),
        billed_kwh=Decimal('100000.0000'),
        billed_max_demand_kva=Decimal('1600.00'),
        billed_amount_inr=Decimal('800000.00'),
        auto_reconcile=False
    )
    assert bill.effective_cost_per_kwh_inr == Decimal('8.0000')

@pytest.mark.django_db
def test_reconciliation_within_tolerance(billing_setup):
    admin, fac, tariff = billing_setup
    # Metered is exactly 100,000 kWh.
    # Billed 100,500 kWh -> discrepancy = 500 kWh (0.50% <= 1.0%) -> 'verified_within_tolerance'
    bill = record_utility_bill(
        facility=fac,
        tariff=tariff,
        bill_number='BILL-TOLERANCE',
        billing_cycle_start=date(2026, 3, 1),
        billing_cycle_end=date(2026, 3, 10),
        due_date=date(2026, 3, 25),
        billed_kwh=Decimal('100500.0000'),
        billed_max_demand_kva=Decimal('1600.00'),
        billed_amount_inr=Decimal('804000.00'),
        auto_reconcile=True
    )
    rec = bill.reconciliation
    assert rec.metered_kwh == Decimal('100000.0000')
    assert rec.discrepancy_kwh == Decimal('500.0000')
    assert rec.discrepancy_percentage == Decimal('0.50')
    assert rec.reconciliation_status == 'verified_within_tolerance'

@pytest.mark.django_db
def test_reconciliation_action_required_variance(billing_setup):
    admin, fac, tariff = billing_setup
    # Metered is 100,000 kWh.
    # Billed 105,000 kWh -> discrepancy = 5,000 kWh (4.76% > 2.5%) -> 'variance_action_required'
    bill = record_utility_bill(
        facility=fac,
        tariff=tariff,
        bill_number='BILL-ACTION-REQ',
        billing_cycle_start=date(2026, 3, 1),
        billing_cycle_end=date(2026, 3, 10),
        due_date=date(2026, 3, 25),
        billed_kwh=Decimal('105000.0000'),
        billed_max_demand_kva=Decimal('1600.00'),
        billed_amount_inr=Decimal('840000.00'),
        auto_reconcile=True
    )
    rec = bill.reconciliation
    assert rec.discrepancy_percentage == Decimal('4.76')
    assert rec.reconciliation_status == 'variance_action_required'
    # Variance cost = 5,000 kWh * 8.0 = ₹40,000.00
    assert rec.variance_cost_inr == Decimal('40000.00')


# ---------- manual bill entry permissions ----------

def _bill_payload(fac, tariff, number):
    return {
        'facility': fac.id,
        'tariff': tariff.id,
        'bill_number': number,
        'billing_cycle_start': '2026-03-01',
        'billing_cycle_end': '2026-03-10',
        'due_date': '2026-03-25',
        'billed_kwh': '100000.0000',
        'billed_max_demand_kva': '1500.00',
        'billed_amount_inr': '800000.00',
        'payment_status': 'unpaid',
    }


@pytest.mark.django_db
def test_field_engineer_can_record_bill_for_assigned_facility(billing_setup):
    from facilities.models import UserFacilityAssignment
    _, fac, tariff = billing_setup
    eng = CustomUser.objects.create_user(email='eng@gg.in', password='pass', role='field_engineer')
    UserFacilityAssignment.objects.create(user=eng, facility=fac)
    client = APIClient()
    client.force_authenticate(user=eng)
    res = client.post('/api/v1/billing/bills/', _bill_payload(fac, tariff, 'BILL-ENG-1'), format='json')
    assert res.status_code == 201
    assert UtilityBill.objects.filter(bill_number='BILL-ENG-1').exists()


@pytest.mark.django_db
def test_field_engineer_cannot_record_bill_for_unassigned_facility(billing_setup):
    _, fac, tariff = billing_setup
    eng = CustomUser.objects.create_user(email='eng2@gg.in', password='pass', role='field_engineer')
    client = APIClient()
    client.force_authenticate(user=eng)
    res = client.post('/api/v1/billing/bills/', _bill_payload(fac, tariff, 'BILL-ENG-2'), format='json')
    assert res.status_code == 404
    assert not UtilityBill.objects.filter(bill_number='BILL-ENG-2').exists()


@pytest.mark.django_db
def test_customer_cannot_record_bill(billing_setup):
    from facilities.models import UserFacilityAssignment
    _, fac, tariff = billing_setup
    cust = CustomUser.objects.create_user(email='cust@gg.in', password='pass', role='customer')
    UserFacilityAssignment.objects.create(user=cust, facility=fac)
    client = APIClient()
    client.force_authenticate(user=cust)
    res = client.post('/api/v1/billing/bills/', _bill_payload(fac, tariff, 'BILL-CUST'), format='json')
    assert res.status_code == 403
    assert res.json()['error']['code'] == 'PERMISSION_DENIED'
