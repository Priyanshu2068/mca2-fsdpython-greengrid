from django.core.management.base import BaseCommand
from facilities.models import Facility
from recommendations.services import generate_recommendations_for_facility, generate_all_recommendations

class Command(BaseCommand):
    help = 'Executes deterministic ECM rules to generate actionable energy recommendations with ₹ savings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--facility-id',
            type=int,
            default=None,
            help='Optional facility ID to evaluate recommendations for a single site.'
        )

    def handle(self, *args, **options):
        facility_id = options.get('facility_id')
        if facility_id:
            try:
                fac = Facility.objects.get(id=facility_id)
            except Facility.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Facility with ID {facility_id} does not exist."))
                return

            self.stdout.write(self.style.NOTICE(f"Generating recommendations for facility '{fac.name}'..."))
            recoms = generate_recommendations_for_facility(fac)
            self.stdout.write(self.style.SUCCESS(f"Generated/updated {len(recoms)} recommendations for {fac.name}."))
        else:
            self.stdout.write(self.style.NOTICE("Generating recommendations across all registered facilities..."))
            count = generate_all_recommendations()
            self.stdout.write(self.style.SUCCESS(f"Successfully generated/updated {count} recommendations."))
