"""
Management command to run the environmental simulator for a facility.
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from facilities.models import Facility
from simulator.simulator import EnvironmentalSimulator

class Command(BaseCommand):
    help = 'Runs the built-in load simulator to generate 15-minute meter readings.'

    def add_arguments(self, parser):
        parser.add_argument('--facility-id', type=int, required=True, help='ID of target Facility')
        parser.add_argument('--days', type=int, default=1, help='Number of days to simulate (default: 1)')
        parser.add_argument('--start-date', type=str, default=None, help='Start date YYYY-MM-DD (default: yesterday)')

    def handle(self, *args, **options):
        facility_id = options['facility_id']
        days = options['days']
        start_date_str = options['start_date']

        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise CommandError(f"Facility with ID {facility_id} does not exist.")

        if start_date_str:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            except ValueError:
                raise CommandError("start-date must be in YYYY-MM-DD format.")
        else:
            now = timezone.now()
            start_date = timezone.make_aware(datetime(now.year, now.month, now.day)) - timedelta(days=days)

        self.stdout.write(self.style.NOTICE(
            f"Simulating {days} days of telemetry for '{facility.name}' starting {start_date.strftime('%Y-%m-%d')}..."
        ))

        sim = EnvironmentalSimulator(facility)
        result = sim.run(start_date=start_date, days=days)

        self.stdout.write(self.style.SUCCESS(
            f"Simulator complete: {result.get('accepted', 0)} accepted, "
            f"{result.get('duplicates_ignored', 0)} duplicates, "
            f"{result.get('rejected', 0)} rejected. Duration: {result.get('duration_ms', 0)}ms."
        ))

