from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

SERVICE_CHECKS_TOTAL = Counter(
    'netops_service_checks_total',
    'Total service checks',
    ['service_name', 'status'],
)

SERVICE_RESPONSE_TIME = Histogram(
    'netops_service_response_time_seconds',
    'Response time in seconds',
    ['service_name'],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

SERVICES_UP = Gauge('netops_services_up', 'Services currently up')
SERVICES_DOWN = Gauge('netops_services_down', 'Services currently down')


def record_check(service_name, status, response_time_ms):
    SERVICE_CHECKS_TOTAL.labels(service_name=service_name, status=status).inc()
    SERVICE_RESPONSE_TIME.labels(service_name=service_name).observe(response_time_ms / 1000)


def update_gauges(up_count, down_count):
    SERVICES_UP.set(up_count)
    SERVICES_DOWN.set(down_count)


def metrics_view(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)