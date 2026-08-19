from rest_framework import serializers
from .models import Widget


class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ['id', 'widget_type', 'title', 'description', 'form_fields',
                   'button_text', 'display_options', 'bundle_version', 'is_active',
                   'created_at', 'updated_at']
        read_only_fields = ['id', 'bundle_version', 'created_at', 'updated_at']


class WidgetConfigSerializer(serializers.ModelSerializer):
    """What the public embed script actually receives — deliberately narrower
    than WidgetSerializer. No tenant info, no internal flags leak to the browser."""
    class Meta:
        model = Widget
        fields = ['id', 'widget_type', 'title', 'description', 'form_fields',
                   'button_text', 'display_options']