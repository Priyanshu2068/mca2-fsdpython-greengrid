import pytest
from decimal import Decimal
from django.utils import timezone
from facilities.models import Facility
from renewables.models import GridEvent
from core.management.commands.seed_demo import Command


@pytest.mark.django_db
def test_demo_grid_events_are_created_once_and_aligned_to_the_meter_grid():
    fac = Facility.objects.create(
        name='Seed Site', code='FAC-SEED', facility_type='tech_park', gross_floor_area_sqm=Decimal('5000.00'),
        address='x', city='x', state='x', pin_code='1')
    cmd = Command()
    now = timezone.now()

    cmd._events(fac, now)
    first = GridEvent.objects.filter(facility=fac).count()
    assert first == 4

    # re-running the seed must not add the same events again
    cmd._events(fac, now)
    cmd._events(fac, now)
    assert GridEvent.objects.filter(facility=fac).count() == first

    # outages start on a 15-minute mark so they line up with the readings
    assert all(e.start_time.minute % 15 == 0 and e.start_time.second == 0 for e in GridEvent.objects.filter(facility=fac))
