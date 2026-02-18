"""
  python manage.py run_checks
  python manage.py run_checks --continuous --interval 30
"""
import signal
import time

from django.core.management.base import BaseCommand

from monitor.metrics import record_check, update_gauges
from monitor.services import ServiceChecker


class Command(BaseCommand):
    help = 'Run service health checks'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False

    def add_arguments(self, parser):
        parser.add_argument('--continuous', action='store_true')
        parser.add_argument('--interval', type=int, default=60)

    def handle(self, *args, **options):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        checker = ServiceChecker()
        while not self._shutdown:
            results = checker.check_all_active()
            up = sum(1 for r in results if r.status == 'up')
            down = len(results) - up
            update_gauges(up, down)

            for r in results:
                record_check(r.service.name, r.status, r.response_time_ms)
                icon = '\u2713' if r.status == 'up' else '\u2717'
                self.stdout.write(f"  {icon} {r.service.name}: {r.status} ({r.response_time_ms:.0f}ms)")

            self.stdout.write(self.style.SUCCESS(f"Checked {len(results)}: {up} up, {down} down"))

            if not options['continuous']:
                break
            time.sleep(options['interval'])

        if self._shutdown:
            self.stdout.write(self.style.WARNING("Shutting down gracefully..."))

    def _handle_signal(self, signum, frame):
        self._shutdown = True
