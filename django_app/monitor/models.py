"""
MSP kontextus: Minden ügyfélnek külön ServiceTarget-jei lennének.
Valódi rendszerben Customer FK kapcsolódna ide.
"""
from django.db import models
from django.utils import timezone


class ServiceTarget(models.Model):
    class Status(models.TextChoices):
        UP = 'up', 'Up'
        DOWN = 'down', 'Down'
        UNKNOWN = 'unknown', 'Unknown'

    name = models.CharField(max_length=200)
    url = models.URLField()
    check_interval = models.IntegerField(default=60, help_text="seconds")
    timeout = models.IntegerField(default=10)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNKNOWN)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

    class Meta:
        ordering = ['name']


class CheckResult(models.Model):
    service = models.ForeignKey(ServiceTarget, on_delete=models.CASCADE, related_name='results')
    status = models.CharField(max_length=10, choices=ServiceTarget.Status.choices)
    response_time_ms = models.FloatField(null=True)
    status_code = models.IntegerField(null=True)
    error_message = models.TextField(blank=True, default='')
    checked_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.service.name}: {self.status} ({self.response_time_ms}ms)"

    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['service', '-checked_at']),
        ]