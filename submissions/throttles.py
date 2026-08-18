from rest_framework.throttling import SimpleRateThrottle


class SubmissionIPThrottle(SimpleRateThrottle):
    scope = 'submission_ip'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class SubmissionWidgetThrottle(SimpleRateThrottle):
    scope = 'submission_widget'

    def get_cache_key(self, request, view):
        widget_id = request.data.get('widget_id')
        if not widget_id:
            return None  # let the serializer reject a missing widget_id, not the throttle
        return self.cache_format % {'scope': self.scope, 'ident': widget_id}