from django.contrib import admin
from .models import ServiceTarget, CheckResult

@admin.register(ServiceTarget)
class ServiceTargetAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'status', 'is_active', 'updated_at']
    list_filter = ['status', 'is_active']

@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ['service', 'status', 'response_time_ms', 'status_code', 'checked_at']
    list_filter = ['status']