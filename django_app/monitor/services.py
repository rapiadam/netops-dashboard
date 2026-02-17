import time
import requests
from .models import ServiceTarget, CheckResult


class ServiceChecker:
    def check_service(self, target: ServiceTarget) -> CheckResult:
        start = time.time()
        status = ServiceTarget.Status.DOWN
        status_code = None
        error = ''

        try:
            resp = requests.get(
                target.url,
                timeout=target.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'NetOps-Monitor/1.0'},
            )
            status_code = resp.status_code
            if 200 <= status_code < 400:
                status = ServiceTarget.Status.UP
            else:
                error = f"HTTP {status_code}"
        except requests.ConnectionError as e:
            error = f"Connection error: {str(e)[:200]}"
        except requests.Timeout:
            error = f"Timeout after {target.timeout}s"
        except requests.RequestException as e:
            error = f"Error: {str(e)[:200]}"

        elapsed_ms = (time.time() - start) * 1000

        result = CheckResult.objects.create(
            service=target,
            status=status,
            response_time_ms=round(elapsed_ms, 2),
            status_code=status_code,
            error_message=error,
        )

        target.status = status
        target.save(update_fields=['status', 'updated_at'])
        return result

    def check_all_active(self) -> list[CheckResult]:
        targets = ServiceTarget.objects.filter(is_active=True)
        return [self.check_service(t) for t in targets]