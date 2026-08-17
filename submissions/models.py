import uuid
from django.db import models
from accounts.models import Tenant
from widgets.models import Widget


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Denormalized tenant FK (not just via widget.tenant) so every submissions
    # query can filter directly on tenant without an extra join — this is the
    # tenant-isolation check we'll enforce in every queryset in Phase 2/3.
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='submissions')
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name='submissions')

    data = models.JSONField()               # the actual form field values, post-validation

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    geo_provider_used = models.CharField(max_length=50, blank=True)   # 'ip-api' / 'ipapi.co' / '' if all failed

    honeypot_triggered = models.BooleanField(default=False)
    side_effect_sent = models.BooleanField(default=False)   # did the email/webhook fire successfully

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'widget', '-created_at']),
        ]