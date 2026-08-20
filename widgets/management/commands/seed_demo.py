from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Tenant, TenantMembership
from widgets.models import Widget
from submissions.models import Submission


class Command(BaseCommand):
    help = "Seed demo data: one tenant, one owner, one widget, a few submissions."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='demoowner')
        if created:
            user.set_password('demopass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo user: demoowner / demopass123'))
        else:
            self.stdout.write('Demo user already exists (demoowner / demopass123).')

        tenant, _ = Tenant.objects.get_or_create(name='Demo Co')
        TenantMembership.objects.get_or_create(user=user, tenant=tenant, defaults={'role': 'owner'})

        widget, created = Widget.objects.get_or_create(
            tenant=tenant,
            title='Demo Newsletter Signup',
            defaults={
                'widget_type': 'signup_form',
                'description': 'Join our demo newsletter',
                'form_fields': [{'name': 'email', 'type': 'email', 'required': True}],
                'button_text': 'Subscribe',
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Widget ready: {widget.id}') if created
                           else f'Demo widget already exists: {widget.id}')

        if not Submission.objects.filter(tenant=tenant).exists():
            for email in ['alice@example.com', 'bob@example.com', 'carol@example.com']:
                Submission.objects.create(tenant=tenant, widget=widget, data={'email': email})
            self.stdout.write(self.style.SUCCESS('Created 3 demo submissions.'))
        else:
            self.stdout.write('Demo submissions already exist.')

        self.stdout.write(self.style.SUCCESS(
            f"\nDemo ready.\n"
            f"  Login: demoowner / demopass123\n"
            f"  Widget ID: {widget.id}\n"
            f"  Embed snippet:\n"
            f'  <script src="http://localhost:8000/widget.js" data-widget-id="{widget.id}"></script>\n'
        ))