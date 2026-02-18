from rest_framework import serializers
from .models import ServiceTarget, CheckResult


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = ['status', 'response_time_ms', 'status_code', 'error_message', 'checked_at']


class ServiceTargetSerializer(serializers.ModelSerializer):
    last_result = serializers.SerializerMethodField()

    class Meta:
        model = ServiceTarget
        fields = ['id', 'name', 'url', 'status', 'is_active', 'check_interval', 'updated_at', 'last_result']

    def get_last_result(self, obj):
        if hasattr(obj, '_prefetched_last_result'):
            results = obj._prefetched_last_result
            if results:
                return CheckResultSerializer(results[0]).data
        latest = obj.results.first()
        if latest:
            return CheckResultSerializer(latest).data
        return None


class RunCheckResultSerializer(serializers.Serializer):
    service = serializers.CharField(source='service.name')
    status = serializers.CharField()
    ms = serializers.FloatField(source='response_time_ms')
