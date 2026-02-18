from unittest.mock import patch, MagicMock

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import ServiceTarget, CheckResult
from .services import ServiceChecker

User = get_user_model()


class ServiceTargetModelTest(TestCase):
    def test_str_representation(self):
        target = ServiceTarget.objects.create(name="Test", url="https://example.com")
        self.assertEqual(str(target), "Test (unknown)")

    def test_default_values(self):
        target = ServiceTarget.objects.create(name="Test", url="https://example.com")
        self.assertEqual(target.status, ServiceTarget.Status.UNKNOWN)
        self.assertTrue(target.is_active)
        self.assertEqual(target.check_interval, 60)
        self.assertEqual(target.timeout, 10)

    def test_ordering(self):
        ServiceTarget.objects.create(name="Bravo", url="https://b.com")
        ServiceTarget.objects.create(name="Alpha", url="https://a.com")
        names = list(ServiceTarget.objects.values_list('name', flat=True))
        self.assertEqual(names, ["Alpha", "Bravo"])


class CheckResultModelTest(TestCase):
    def setUp(self):
        self.target = ServiceTarget.objects.create(name="Test", url="https://example.com")

    def test_str_representation(self):
        result = CheckResult.objects.create(
            service=self.target, status='up', response_time_ms=42.5
        )
        self.assertIn("Test", str(result))
        self.assertIn("up", str(result))

    def test_ordering_newest_first(self):
        r1 = CheckResult.objects.create(service=self.target, status='up', response_time_ms=10)
        r2 = CheckResult.objects.create(service=self.target, status='down', response_time_ms=20)
        results = list(self.target.results.all())
        self.assertEqual(results[0], r2)
        self.assertEqual(results[1], r1)

    def test_cascade_delete(self):
        CheckResult.objects.create(service=self.target, status='up', response_time_ms=10)
        self.target.delete()
        self.assertEqual(CheckResult.objects.count(), 0)


class ServiceCheckerTest(TestCase):
    def setUp(self):
        self.target = ServiceTarget.objects.create(
            name="Test Service", url="https://example.com", timeout=5
        )
        self.checker = ServiceChecker()

    @patch('monitor.services.requests.get')
    def test_check_service_up(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        result = self.checker.check_service(self.target)

        self.assertEqual(result.status, 'up')
        self.assertIsNotNone(result.response_time_ms)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.error_message, '')
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, 'up')

    @patch('monitor.services.requests.get')
    def test_check_service_down_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        result = self.checker.check_service(self.target)

        self.assertEqual(result.status, 'down')
        self.assertEqual(result.status_code, 500)
        self.assertIn("HTTP 500", result.error_message)

    @patch('monitor.services.requests.get')
    def test_check_service_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        result = self.checker.check_service(self.target)

        self.assertEqual(result.status, 'down')
        self.assertIn("Connection error", result.error_message)

    @patch('monitor.services.requests.get')
    def test_check_service_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout()

        result = self.checker.check_service(self.target)

        self.assertEqual(result.status, 'down')
        self.assertIn("Timeout", result.error_message)

    @patch('monitor.services.requests.get')
    def test_check_all_active_skips_inactive(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        ServiceTarget.objects.create(name="Inactive", url="https://inactive.com", is_active=False)

        results = self.checker.check_all_active()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].service.name, "Test Service")

    @patch('monitor.services.requests.get')
    def test_check_creates_result_and_updates_target(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        self.checker.check_service(self.target)

        self.assertEqual(CheckResult.objects.count(), 1)
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, 'up')


class HealthViewTest(TestCase):
    def test_health_endpoint(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'ok')

    def test_health_no_auth_required(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)


class DashboardAPIViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_requires_authentication(self):
        client = APIClient()
        resp = client.get('/api/v1/dashboard/')
        self.assertIn(resp.status_code, [401, 403])

    def test_dashboard_empty(self):
        resp = self.client.get('/api/v1/dashboard/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['summary']['total'], 0)
        self.assertEqual(data['services'], [])

    def test_dashboard_with_services(self):
        ServiceTarget.objects.create(name="Svc1", url="https://a.com", status='up')
        ServiceTarget.objects.create(name="Svc2", url="https://b.com", status='down')

        resp = self.client.get('/api/v1/dashboard/')
        data = resp.json()
        self.assertEqual(data['summary']['total'], 2)
        self.assertEqual(data['summary']['up'], 1)
        self.assertEqual(data['summary']['down'], 1)
        self.assertEqual(len(data['services']), 2)


class RunChecksViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_requires_authentication(self):
        client = APIClient()
        resp = client.post('/api/v1/check/')
        self.assertIn(resp.status_code, [401, 403])

    @patch('monitor.services.requests.get')
    def test_run_checks(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        ServiceTarget.objects.create(name="Test", url="https://example.com")

        resp = self.client.post('/api/v1/check/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['checked'], 1)
        self.assertEqual(len(data['results']), 1)
