import uuid
from django.db import models
from accounts.models import Tenant


class Widget(models.Model):
    TYPE_SIGNUP = 'signup_form'
    TYPE_CTA = 'cta'
    TYPE_POPOVER = 'popover'
    TYPE_CHOICES = [
        (TYPE_SIGNUP, 'Signup form'),
        (TYPE_CTA, 'Call to action'),
        (TYPE_POPOVER, 'Popover'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='widgets')

    widget_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    form_fields = models.JSONField(default=list)      # [{"name": "email", "type": "email", "required": true}, ...]
    button_text = models.CharField(max_length=100, default='Submit')
    display_options = models.JSONField(default=dict)   # theme, position, delay, etc.

    bundle_version = models.PositiveIntegerField(default=1)  # bumped on JS behavior changes -> cache bust
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f'{self.title} ({self.tenant})'