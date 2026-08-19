from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Tenant, TenantMembership
from widgets.models import Widget


class WidgetConfigTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Co")
        self.widget = Widget.objects.create(
            tenant=self.tenant, widget_type="signup_form", title="Join us",
            form_fields=[{"name": "email", "type": "email", "required": True}],
        )

    def test_config_endpoint_returns_public_shape(self):
        response = self.client.get(f'/api/widgets/{self.widget.id}/config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['title'], "Join us")
        self.assertNotIn('tenant', data)          # tenant must never leak to the public config

    def test_inactive_widget_returns_404(self):
        self.widget.is_active = False
        self.widget.save()
        response = self.client.get(f'/api/widgets/{self.widget.id}/config/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_config_endpoint_has_cache_headers(self):
        response = self.client.get(f'/api/widgets/{self.widget.id}/config/')
        self.assertIn('ETag', response)
        self.assertIn('Cache-Control', response)


class WidgetTenantIsolationTests(TestCase):
    """The non-negotiable rule: a tenant must never see or touch another
    tenant's widgets, even with a valid, authenticated token."""

    def setUp(self):
        self.client = APIClient()

        self.tenant_a = Tenant.objects.create(name="Tenant A")
        self.user_a = User.objects.create_user(username="usera", password="pass12345")
        TenantMembership.objects.create(user=self.user_a, tenant=self.tenant_a, role='owner')
        self.widget_a = Widget.objects.create(
            tenant=self.tenant_a, widget_type="signup_form", title="A's widget",
            form_fields=[{"name": "email", "type": "email", "required": True}],
        )

        self.tenant_b = Tenant.objects.create(name="Tenant B")
        self.user_b = User.objects.create_user(username="userb", password="pass12345")
        TenantMembership.objects.create(user=self.user_b, tenant=self.tenant_b, role='owner')
        self.widget_b = Widget.objects.create(
            tenant=self.tenant_b, widget_type="signup_form", title="B's widget",
            form_fields=[{"name": "email", "type": "email", "required": True}],
        )

    def test_user_cannot_list_other_tenants_widgets(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/widgets/')
        ids = [w['id'] for w in response.json()['results']] if 'results' in response.json() else [w['id'] for w in response.json()]
        self.assertIn(str(self.widget_a.id), ids)
        self.assertNotIn(str(self.widget_b.id), ids)

    def test_user_cannot_retrieve_other_tenants_widget_by_id(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f'/api/widgets/{self.widget_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_tenants_widget(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(f'/api/widgets/{self.widget_b.id}/', {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.widget_b.refresh_from_db()
        self.assertEqual(self.widget_b.title, "B's widget")  # unchanged

    def test_user_cannot_delete_other_tenants_widget(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(f'/api/widgets/{self.widget_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Widget.objects.filter(id=self.widget_b.id).exists())

    def test_created_widget_auto_scoped_to_own_tenant(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/widgets/', {
            'widget_type': 'cta', 'title': 'New widget',
            'form_fields': [], 'button_text': 'Go',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Widget.objects.get(id=response.json()['id'])
        self.assertEqual(created.tenant, self.tenant_a)