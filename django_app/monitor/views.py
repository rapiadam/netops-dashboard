import logging

from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ServiceTarget, CheckResult
from .serializers import ServiceTargetSerializer, RunCheckResultSerializer
from .services import ServiceChecker
from .metrics import record_check, update_gauges

logger = logging.getLogger('monitor')


class HealthView(APIView):
    """Docker HEALTHCHECK + load balancer endpoint."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'netops-dashboard'})


class DashboardAPIView(APIView):
    """Dashboard data with service summary and details."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        last_result_qs = CheckResult.objects.order_by('-checked_at')
        services = ServiceTarget.objects.prefetch_related(
            Prefetch('results', queryset=last_result_qs[:1], to_attr='_prefetched_last_result')
        )
        serializer = ServiceTargetSerializer(services, many=True)
        summary = {
            'total': services.count(),
            'up': services.filter(status='up').count(),
            'down': services.filter(status='down').count(),
        }
        return Response({'summary': summary, 'services': serializer.data})


class RunChecksView(APIView):
    """Trigger health checks for all active services."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            checker = ServiceChecker()
            results = checker.check_all_active()

            up = sum(1 for r in results if r.status == 'up')
            down = len(results) - up
            update_gauges(up, down)
            for r in results:
                record_check(r.service.name, r.status, r.response_time_ms)

            serializer = RunCheckResultSerializer(results, many=True)
            return Response({'checked': len(results), 'results': serializer.data})
        except Exception:
            logger.exception("Error running service checks")
            return Response(
                {'error': 'Failed to run checks'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
