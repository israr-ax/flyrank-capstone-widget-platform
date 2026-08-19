from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from submissions.throttles import SubmissionIPThrottle, SubmissionWidgetThrottle

from accounts.models import Tenant
from widgets.models import Widget
from submissions.models import Submission
from submissions import enrichment
from django.core.cache import cache

class SubmissionTestBase(TestCase):
    def setUp(self):
        cache.clear()   # throttle counts persist across tests unless cleared explicitly
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Co")
        self.widget = Widget.objects.create(
            tenant=self.tenant,
            widget_type="signup_form",
            title="Newsletter",
            form_fields=[{"name": "email", "type": "email", "required": True}],
        )
        self.url = "/api/submissions/"

class SubmissionTestBase(TestCase):
    def setUp(self):
        cache.clear()   # throttle counts persist across tests unless cleared explicitly
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Co")
        self.widget = Widget.objects.create(
            tenant=self.tenant,
            widget_type="signup_form",
            title="Newsletter",
            form_fields=[{"name": "email", "type": "email", "required": True}],
        )
        self.url = "/api/submissions/"

    def valid_payload(self, **overrides):
        payload = {
            "widget_id": str(self.widget.id),
            "data": {"email": "test@example.com"},
            "hp_field": "",
        }
        payload.update(overrides)
        return payload


class CORSPreflightTests(SubmissionTestBase):
    def test_preflight_returns_allow_origin_header(self):
        response = self.client.options(
            self.url,
            HTTP_ORIGIN="http://localhost:5500",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", {k.lower(): v for k, v in response.items()})


class InvalidPayloadTests(SubmissionTestBase):
    def test_missing_required_field_returns_400(self):
        response = self.client.post(self.url, data={
            "widget_id": str(self.widget.id),
            "data": {},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.json())

    def test_unknown_widget_id_returns_400(self):
        response = self.client.post(self.url, data={
            "widget_id": "00000000-0000-0000-0000-000000000000",
            "data": {"email": "a@b.com"},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_field_rejected(self):
        response = self.client.post(self.url, data=self.valid_payload(
            data={"email": "a@b.com", "not_a_real_field": "x"}
        ), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OversizedPayloadTests(SubmissionTestBase):
    def test_oversized_body_rejected(self):
        huge_value = "A" * (25 * 1024)  # exceeds DATA_UPLOAD_MAX_MEMORY_SIZE (20KB)
        response = self.client.post(self.url, data=self.valid_payload(
            data={"email": huge_value}
        ), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HoneypotTests(SubmissionTestBase):
    def test_honeypot_triggered_does_not_create_row(self):
        before = Submission.objects.count()
        response = self.client.post(self.url, data=self.valid_payload(
            hp_field="i am a bot"
        ), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # bot sees fake success
        self.assertEqual(Submission.objects.count(), before)  # but nothing was actually stored



class RateLimitTests(SubmissionTestBase):
    def test_ip_throttle_returns_429_after_burst(self):
        test_rates = {'submission_ip': '3/min', 'submission_widget': '100/min'}

        with patch.object(SubmissionIPThrottle, 'THROTTLE_RATES', test_rates), \
             patch.object(SubmissionWidgetThrottle, 'THROTTLE_RATES', test_rates):

            for _ in range(3):
                response = self.client.post(self.url, data=self.valid_payload(), format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = self.client.post(self.url, data=self.valid_payload(), format="json")
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class GeoFallbackTests(SubmissionTestBase):
    def test_provider_a_fails_provider_b_succeeds(self):
        def fail_a(ip):
            raise ValueError("provider A down")

        def succeed_b(ip):
            return {"country": "Pakistan", "city": "Karachi", "provider": "ipapi.co"}

        with patch.object(enrichment, "PROVIDERS", [fail_a, succeed_b]):
            response = self.client.post(self.url, data=self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get(id=response.json()["id"])
        self.assertEqual(submission.country, "Pakistan")
        self.assertEqual(submission.geo_provider_used, "ipapi.co")

    def test_all_providers_fail_submission_still_succeeds(self):
        def fail_a(ip):
            raise ValueError("down")

        def fail_b(ip):
            raise ValueError("down")

        with patch.object(enrichment, "PROVIDERS", [fail_a, fail_b]):
            response = self.client.post(self.url, data=self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get(id=response.json()["id"])
        self.assertEqual(submission.country, "")
        self.assertEqual(submission.geo_provider_used, "")



class SideEffectFailureTests(SubmissionTestBase):
    def test_failing_side_effect_does_not_block_submission(self):
        with patch("submissions.views.send_confirmation", side_effect=Exception("SMTP down")):
            response = self.client.post(self.url, data=self.valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        