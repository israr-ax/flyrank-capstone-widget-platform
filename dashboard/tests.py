from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Tenant, TenantMembership
from widgets.models import Widget
from submissions.models import Submission


class DashboardTenantIsolationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.tenant_a = Tenant.objects.create(name="Tenant A")
        self.user_a = User.objects.create_user(username="usera", password="pass12345")
        TenantMembership.objects.create(user=self.user_a, tenant=self.tenant_a, role='owner')
        self.widget_a = Widget.objects.create(
            tenant=self.tenant_a, widget_type="signup_form", title="A's widget", form_fields=[],
        )
        Submission.objects.create(tenant=self.tenant_a, widget=self.widget_a, data={"email": "a@a.com"})

        self.tenant_b = Tenant.objects.create(name="Tenant B")
        self.user_b = User.objects.create_user(username="userb", password="pass12345")
        TenantMembership.objects.create(user=self.user_b, tenant=self.tenant_b, role='owner')
        self.widget_b = Widget.objects.create(
            tenant=self.tenant_b, widget_type="signup_form", title="B's widget", form_fields=[],
        )
        # Tenant B gets THREE submissions — if isolation is broken, A's stats would be inflated
        for i in range(3):
            Submission.objects.create(tenant=self.tenant_b, widget=self.widget_b, data={"email": f"b{i}@b.com"})

    def test_dashboard_only_counts_own_tenant_submissions(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body['total_submissions'], 1)
        self.assertEqual(body['total_widgets'], 1)
        self.assertEqual(len(body['submissions_by_widget']), 1)
        self.assertEqual(body['submissions_by_widget'][0]['widget__title'], "A's widget")

    def test_unauthenticated_request_rejected(self):
        response = self.client.get('/api/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
from django.test import TestCase
from rest_framework.test import APIClient


class CORSSurfaceTests(TestCase):
    """Public embed surfaces must expose CORS headers to any origin.
    Admin/authenticated surfaces must NOT — proves the split actually works."""

    def setUp(self):
        self.client = APIClient()

    def test_submission_endpoint_has_cors_headers(self):
        response = self.client.options(
            '/api/submissions/',
            HTTP_ORIGIN='http://some-random-customer-site.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertIn('access-control-allow-origin', {k.lower(): v for k, v in response.items()})

    def test_dashboard_endpoint_has_no_cors_headers(self):
        response = self.client.options(
            '/api/dashboard/stats/',
            HTTP_ORIGIN='http://some-random-customer-site.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
        )
        headers = {k.lower(): v for k, v in response.items()}
        self.assertNotIn('access-control-allow-origin', headers)