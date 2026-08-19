from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.utils import get_tenant_for_user
from submissions.models import Submission
from widgets.models import Widget


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_tenant_for_user(request.user)

        submissions = Submission.objects.filter(tenant=tenant)

        per_widget = list(
            submissions.values('widget__id', 'widget__title')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        per_country = list(
            submissions.exclude(country='')
            .values('country')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'total_widgets': Widget.objects.filter(tenant=tenant).count(),
            'total_submissions': submissions.count(),
            'submissions_by_widget': per_widget,
            'submissions_by_country': per_country,
        })