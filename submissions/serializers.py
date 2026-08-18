from rest_framework import serializers
from widgets.models import Widget

MAX_PAYLOAD_FIELDS = 30
MAX_FIELD_VALUE_LENGTH = 2000


class SubmissionCreateSerializer(serializers.Serializer):
    widget_id = serializers.UUIDField()
    data = serializers.DictField(
        child=serializers.CharField(allow_blank=True, max_length=MAX_FIELD_VALUE_LENGTH)
    )
    hp_field = serializers.CharField(required=False, allow_blank=True, default='')  # honeypot trap

    def validate_widget_id(self, value):
        try:
            widget = Widget.objects.select_related('tenant').get(id=value, is_active=True)
        except Widget.DoesNotExist:
            raise serializers.ValidationError('Widget not found or inactive.')
        self.widget = widget
        return value

    def validate_data(self, value):
        if len(value) > MAX_PAYLOAD_FIELDS:
            raise serializers.ValidationError('Too many fields in payload.')
        return value

    def validate(self, attrs):
        widget = getattr(self, 'widget', None)
        if widget is None:
            return attrs

        required_names = {f['name'] for f in widget.form_fields if f.get('required')}
        allowed_names = {f['name'] for f in widget.form_fields}
        submitted = attrs.get('data', {})

        missing = required_names - submitted.keys()
        if missing:
            raise serializers.ValidationError({'data': f'Missing required fields: {sorted(missing)}'})

        unknown = set(submitted.keys()) - allowed_names
        if unknown:
            raise serializers.ValidationError({'data': f'Unknown fields: {sorted(unknown)}'})

        return attrs