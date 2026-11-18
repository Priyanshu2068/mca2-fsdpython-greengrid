from django.core.management.base import BaseCommand
from analytics.services import compute_hourly_rollups

class Command(BaseCommand):
    help = 'Executes incremental 48-hour hourly energy rollups.'

    def add_arguments(self, parser):
        parser.add_argument('--hours-back', type=int, default=48, help='Rolling window in hours (default: 48)')

    def handle(self, *args, **options):
        hours = options['hours_back']
        self.stdout.write(self.style.NOTICE(f"Computing incremental hourly rollups for the past {hours} hours..."))
        count = compute_hourly_rollups(hours_back=hours)
        self.stdout.write(self.style.SUCCESS(f"Successfully computed/updated {count} hourly rollup buckets."))

