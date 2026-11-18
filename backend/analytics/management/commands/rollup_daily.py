from django.core.management.base import BaseCommand
from analytics.services import compute_daily_rollups

class Command(BaseCommand):
    help = 'Executes incremental daily energy rollups with peak/off-peak segregation.'

    def add_arguments(self, parser):
        parser.add_argument('--days-back', type=int, default=7, help='Rolling window in days (default: 7)')

    def handle(self, *args, **options):
        days = options['days_back']
        self.stdout.write(self.style.NOTICE(f"Computing daily rollups for the past {days} days..."))
        count = compute_daily_rollups(days_back=days)
        self.stdout.write(self.style.SUCCESS(f"Successfully computed/updated {count} daily rollups."))

