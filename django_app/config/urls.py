from django.contrib import admin
from django.urls import path
from monitor.views import HealthView, DashboardAPIView, RunChecksView
from monitor.metrics import metrics_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthView.as_view()),
    path('api/dashboard/', DashboardAPIView.as_view()),
    path('api/check/', RunChecksView.as_view()),
    path('metrics', metrics_view),
]