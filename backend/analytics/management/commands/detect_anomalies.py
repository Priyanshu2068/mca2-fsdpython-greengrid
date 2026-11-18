from django.core.management.base import BaseCommand
from analytics.services import run_anomaly_detection

class Command(BaseCommand):
    help = 'Executes rule-based anomaly detection across all active telemetry meters.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running anomaly detection rules (spike, low PF, DG clash, silent meters)..."))
        alerts = run_anomaly_detection()
        self.stdout.write(self.style.SUCCESS(f"Anomaly detection complete: generated {len(alerts)} new alerts."))

