from django.http import JsonResponse
from django.views import View
from .models import ServiceTarget
from .services import ServiceChecker


class HealthView(View):
    """Docker HEALTHCHECK + load balancer endpoint"""

    def get(self, request):
        return JsonResponse({'status': 'ok', 'service': 'netops-dashboard'})


class DashboardAPIView(View):
    """Dashboard data"""

    def get(self, request):
        services = ServiceTarget.objects.all()
        return JsonResponse({
            'summary': {
                'total': services.count(),
                'up': services.filter(status='up').count(),
                'down': services.filter(status='down').count(),
            },
            'services': [
                {
                    'name': s.name,
                    'url': s.url,
                    'status': s.status,
                    'last_check': s.updated_at.isoformat(),
                    'response_ms': (
                        s.results.first().response_time_ms
                        if s.results.exists() else None
                    ),
                }
                for s in services
            ],
        })


class RunChecksView(View):
    def post(self, request):
        results = ServiceChecker().check_all_active()
        return JsonResponse({
            'checked': len(results),
            'results': [
                {'service': r.service.name, 'status': r.status, 'ms': r.response_time_ms}
                for r in results
            ],
        })
