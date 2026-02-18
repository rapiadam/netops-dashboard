from django.contrib import admin
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from monitor.views import HealthView, DashboardAPIView, RunChecksView
from monitor.metrics import metrics_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthView.as_view()),
    path('api/v1/dashboard/', DashboardAPIView.as_view()),
    path('api/v1/check/', RunChecksView.as_view()),
    path('api/v1/token/', obtain_auth_token, name='api-token'),
    # Backwards compat (unversioned)
    path('api/dashboard/', DashboardAPIView.as_view()),
    path('api/check/', RunChecksView.as_view()),
    path('metrics', metrics_view),
]
