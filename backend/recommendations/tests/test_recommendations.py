import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.core.management import call_command
from accounts.models import CustomUser
from facilities.models import Facility, Meter, UserFacilityAssignment
from analytics.models import AnomalyAlert
from recommendations.models import ECMRule, Recommendation
from recommendations.services import (
    generate_recommendations_for_facility,
    generate_all_recommendations,
    update_recommendation_status,
)

@pytest.fixture
def recom_setup(db):
    admin = CustomUser.objects.create_superuser(email='rec_adm@greengrid.in', password='pass')
    cust1 = CustomUser.objects.create_user(email='rec_cust1@greengrid.in', password='pass', role='customer')
    cust2 = CustomUser.objects.create_user(email='rec_cust2@greengrid.in', password='pass', role='customer')

    fac1 = Facility.objects.create(
        name='Titan Tech Park',
        code='FAC-TITAN-01',
        facility_type='tech_park',
        gross_floor_area_sqm=Decimal('25000.00'),
        address='Electronic City',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560100'
    )
    m1 = Meter.objects.create(
        facility=fac1,
        meter_identifier='MTR-TITAN-INC',
        name='Main Incomer Titan',
        energy_source='grid',
        load_category='main_incomer'
    )

    fac2 = Facility.objects.create(
        name='Cosmos Mall',
        code='FAC-COSMOS-02',
        facility_type='retail_mall',
        gross_floor_area_sqm=Decimal('15000.00'),
        address='Whitefield',
        city='Bengaluru',
        state='Karnataka',
        pin_code='560066'
    )
    m2 = Meter.objects.create(
        facility=fac2,
        meter_identifier='MTR-COSMOS-INC',
        name='Main Incomer Cosmos',
        energy_source='grid',
        load_category='main_incomer'
    )

    # Assign fac1 to cust1, fac2 to cust2
    UserFacilityAssignment.objects.create(user=cust1, facility=fac1)
    UserFacilityAssignment.objects.create(user=cust2, facility=fac2)

    # Add a low PF anomaly alert to fac1 to trigger APFC penalty elimination rule
    AnomalyAlert.objects.create(
        facility=fac1,
        meter=m1,
        anomaly_type='low_power_factor',
        severity='medium',
        observed_value=Decimal('0.8400'),
        baseline_value=Decimal('0.9000'),
        reason='Power factor degraded to 0.840 lag.'
    )

    return {
        'admin': admin,
        'cust1': cust1,
        'cust2': cust2,
        'fac1': fac1,
        'fac2': fac2,
        'm1': m1,
        'm2': m2,
    }

def test_generate_recommendations_service(recom_setup):
    fac1 = recom_setup['fac1']
    recoms = generate_recommendations_for_facility(fac1)

    assert len(recoms) == 5
    rules = {r.rule.rule_code for r in recoms}
    assert 'RULE-PEAK-01' in rules
    assert 'RULE-APFC-02' in rules
    assert 'RULE-HVAC-03' in rules
    assert 'RULE-BASE-04' in rules
    assert 'RULE-DG-05' in rules

    # Verify APFC rule received high penalty savings because low_pf alert was present
    apfc = next(r for r in recoms if r.rule.rule_code == 'RULE-APFC-02')
    assert apfc.estimated_annual_savings_inr >= Decimal('180000.00')
    assert apfc.estimated_payback_months > 0

def test_generate_recommendations_management_command(recom_setup):
    call_command('generate_recommendations')
    # Both facilities should have recommendations generated (5 each = 10 total)
    assert Recommendation.objects.count() == 10

def test_recommendation_lifecycle_accept_and_dismiss(recom_setup):
    fac1 = recom_setup['fac1']
    recoms = generate_recommendations_for_facility(fac1)
    recom = recoms[0]

    # Test Accept
    accepted = update_recommendation_status(recom, status='accepted')
    assert accepted.status == 'accepted'
    assert accepted.actioned_at is not None

    # Test Dismiss without reason fails
    with pytest.raises(Exception):
        update_recommendation_status(recom, status='dismissed', dismissal_reason='')

    # Test Dismiss with valid reason succeeds
    dismissed = update_recommendation_status(
        recom,
        status='dismissed',
        dismissal_reason='Already scheduled for chiller overhaul next quarter.'
    )
    assert dismissed.status == 'dismissed'
    assert 'Already scheduled' in dismissed.dismissal_reason

def test_recommendations_api_endpoints_and_scoping(recom_setup):
    admin = recom_setup['admin']
    cust1 = recom_setup['cust1']
    fac1 = recom_setup['fac1']
    fac2 = recom_setup['fac2']

    call_command('generate_recommendations')

    client = APIClient()

    # 1. Rules list endpoint
    client.force_authenticate(user=admin)
    res_rules = client.get('/api/v1/recommendations/rules/')
    assert res_rules.status_code == 200
    assert len(res_rules.data) == 5

    # 2. Recommendations list - Admin sees all 10
    res_admin = client.get('/api/v1/recommendations/')
    assert res_admin.status_code == 200
    assert len(res_admin.data) == 10

    # 3. Recommendations list - Customer 1 only sees fac1 (5 items)
    client.force_authenticate(user=cust1)
    res_cust1 = client.get('/api/v1/recommendations/')
    assert res_cust1.status_code == 200
    assert len(res_cust1.data) == 5
    for item in res_cust1.data:
        assert item['facility'] == fac1.id

    # 4. Scoping: Customer 1 requesting unassigned fac2 returns 404
    res_unauth = client.get(f'/api/v1/recommendations/?facility_id={fac2.id}')
    assert res_unauth.status_code == 404

    # 5. Customer 1 accepts recommendation
    recom_id = res_cust1.data[0]['id']
    res_accept = client.patch(f'/api/v1/recommendations/{recom_id}/', {'status': 'accepted'})
    assert res_accept.status_code == 200
    assert res_accept.data['status'] == 'accepted'

    # 6. Customer 1 dismisses recommendation without reason -> 400
    res_dismiss_fail = client.patch(f'/api/v1/recommendations/{recom_id}/', {'status': 'dismissed'})
    assert res_dismiss_fail.status_code == 400
    assert res_dismiss_fail.data['error']['code'] == 'VALIDATION_ERROR'

    # 7. Customer 1 dismisses recommendation with reason -> 200
    res_dismiss_ok = client.patch(
        f'/api/v1/recommendations/{recom_id}/',
        {
            'status': 'dismissed',
            'dismissal_reason': 'Capex constraints prevent capacitor replacement this fiscal year.'
        }
    )
    assert res_dismiss_ok.status_code == 200
    assert res_dismiss_ok.data['status'] == 'dismissed'

    # 8. Summary endpoint
    res_summary = client.get('/api/v1/recommendations/summary/')
    assert res_summary.status_code == 200
    assert res_summary.data['total_recommendations'] == 5
    assert res_summary.data['dismissed_count'] == 1


@pytest.mark.parametrize('role,expected', [('customer', 200), ('admin', 200), ('field_engineer', 403)])
def test_recommendation_update_is_role_restricted(recom_setup, role, expected):
    from facilities.models import UserFacilityAssignment
    fac1 = recom_setup['fac1']
    user = CustomUser.objects.create_user(email=f'{role}_rr@greengrid.in', password='pass', role=role)
    UserFacilityAssignment.objects.get_or_create(user=user, facility=fac1)

    call_command('generate_recommendations')
    client = APIClient()
    client.force_authenticate(user=user)
    recom_id = client.get(f'/api/v1/recommendations/?facility_id={fac1.id}').data[0]['id']
    res = client.patch(f'/api/v1/recommendations/{recom_id}/', {'status': 'accepted'})
    assert res.status_code == expected
    if expected == 403:
        assert res.data['error']['code'] == 'PERMISSION_DENIED'
