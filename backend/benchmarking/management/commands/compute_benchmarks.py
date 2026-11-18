from django.core.management.base import BaseCommand
from django.utils import timezone
from benchmarking.services import compute_all_facility_benchmarks

class Command(BaseCommand):
    help = 'Computes annual building Energy Use Intensity (EUI in kWh/m2/year) and BEE Star Ratings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Calendar year for which to compute benchmarks (default: current year)'
        )

    def handle(self, *args, **options):
        year = options['year']
        self.stdout.write(self.style.NOTICE(f"Computing building benchmarks and star ratings for year {year}..."))
        count = compute_all_facility_benchmarks(year=year)
        self.stdout.write(self.style.SUCCESS(f"Successfully evaluated and scored {count} facilities for year {year}."))

