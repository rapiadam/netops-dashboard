"""
  python manage.py run_checks
  python manage.py run_checks --continuous --interval 30
"""
import time
from django.core.management.base import BaseCommand
from monitor.services import ServiceChecker
from monitor.metrics import record_check, update_gauges


class Command(BaseCommand):
    help = 'Run service health checks'

    def add_arguments(self, parser):
        parser.add_argument('--continuous', action='store_true')
        parser.add_argument('--interval', type=int, default=60)

    def handle(self, *args, **options):
        checker = ServiceChecker()
        while True:
            results = checker.check_all_active()
            up = sum(1 for r in results if r.status == 'up')
            down = len(results) - up
            update_gauges(up, down)

            for r in results:
                record_check(r.service.name, r.status, r.response_time_ms)
                icon = '✓' if r.status == 'up' else '✗'
                self.stdout.write(f"  {icon} {r.service.name}: {r.status} ({r.response_time_ms:.0f}ms)")

            self.stdout.write(self.style.SUCCESS(f"Checked {len(results)}: {up} up, {down} down"))

            if not options['continuous']:
                break
            time.sleep(options['interval'])