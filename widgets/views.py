from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.cache import patch_response_headers
from django.shortcuts import get_object_or_404

from accounts.utils import get_tenant_for_user
from .models import Widget
from .serializers import WidgetSerializer, WidgetConfigSerializer


class WidgetViewSet(viewsets.ModelViewSet):
    """Authenticated CRUD. get_queryset is the ONLY place tenant filtering
    happens — every action (list/retrieve/update/delete) routes through it,
    so there's no path that accidentally serves another tenant's widget."""
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_tenant_for_user(self.request.user)
        return Widget.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = get_tenant_for_user(self.request.user)
        serializer.save(tenant=tenant)


class WidgetConfigView(APIView):
    """Public, cached. This is what widget.js fetches on every page load
    that embeds this widget, so it needs to be cheap and cacheable."""
    permission_classes = [AllowAny]

    def get(self, request, widget_id):
        widget = get_object_or_404(Widget, id=widget_id, is_active=True)
        serializer = WidgetConfigSerializer(widget)
        response = Response(serializer.data)
        # bundle_version in the cache key/ETag means a config change invalidates
        # cached copies automatically — no manual cache-busting needed.
        response['ETag'] = f'"{widget.id}-{widget.bundle_version}-{widget.updated_at.timestamp()}"'
        patch_response_headers(response, cache_timeout=300)  # 5 min — balances freshness vs load
        return response